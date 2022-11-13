from typing import Any

from ortools.sat.python import cp_model


class Scheduler:
    def schedule(self, data: dict[str, Any]):
        num_days: int = data["constraints"]["days"]
        num_shifts: int = data["constraints"]["shifts"]
        num_doctors: int = len(data["doctors"])

        model = cp_model.CpModel()
        all_days = set(range(num_days))
        shifts: dict[tuple[int, int, int], cp_model.IntVar] = {}

        not_pref_count: cp_model.IntVar = model.NewIntVar(
            0, num_doctors * 2, "Not preferred"
        )
        pref_factors = []

        # Create shift variables
        for doctor, props in data["doctors"].items():
            prefs = props["prefs"]
            leaves = props["leaves"]
            days = all_days.difference(leaves)
            for day in days:
                for i, shift in enumerate(prefs):
                    shifts[(doctor, day, shift)] = model.NewBoolVar(
                        "shift_%s_%id_%is" % (doctor, day, shift)
                    )
                    pref_factors.append(i * shifts[(doctor, day, shift)])

        # Minimize not preferred shifts
        model.Add(not_pref_count >= sum(pref_factors))
        model.Minimize(not_pref_count)

        # Each doctor works at most once a day
        for doctor, props in data["doctors"].items():
            prefs = props["prefs"]
            leaves = props["leaves"]
            days = all_days.difference(leaves)
            for day in days:
                model.AddAtMostOne(shifts[(doctor, day, s)] for s in prefs)

        # Enforce minimum and maximum doctors
        for shift in range(num_shifts):
            min_doctors: int = data["constraints"]["minDoctors"][shift]
            max_doctors: int = data["constraints"]["maxDoctors"][shift]
            for day in range(num_days):
                num_doctors_in_shift: list[cp_model.IntVar] = []
                for doctor, props in data["doctors"].items():
                    prefs: list[int] = props["prefs"]
                    leaves: list[int] = props["leaves"]
                    if day not in leaves:
                        num_doctors_in_shift.append(shifts[(doctor, day, shift)])
                model.Add(min_doctors <= sum(num_doctors_in_shift))
                model.Add(max_doctors >= sum(num_doctors_in_shift))

        solver = cp_model.CpSolver()
        solver.parameters.linearization_level = 0
        solver.parameters.enumerate_all_solutions = True

        solution_limit = 1
        solution_printer = PartialSolutionGetter(
            data, num_days, shifts, solution_limit, self.set_solution
        )

        solver.Solve(model, solution_printer)

        # Statistics
        return {
            "conflicts": solver.NumConflicts(),
            "branches": solver.NumBranches(),
            "wall_time": solver.WallTime(),
            "solution_count": solution_printer.solution_count(),
        }

    def set_solution(self, solution):
        self.solution = solution


class PartialSolutionGetter(cp_model.CpSolverSolutionCallback):
    def __init__(self, data, num_days, shifts, limit, solution_setter):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._data = data
        self._num_days = num_days
        self._shifts = shifts
        self._solution_count = 0
        self._solution_limit = limit
        self._solution_setter = solution_setter

    def OnSolutionCallback(self):
        self._solution_count += 1

        solution = {}
        for doctor, props in self._data["doctors"].items():
            prefs: list[int] = props["prefs"]
            leaves: set[int] = props["leaves"]
            shifts = []
            for day in range(self._num_days):
                if day in leaves:
                    shifts.append(-1)
                    continue
                for s in prefs:
                    if self.Value(self._shifts[(doctor, day, s)]):
                        shifts.append(s)
                        break
                else:
                    shifts.append(-1)
            solution[doctor] = shifts

        self._solution_setter(solution)

        if self._solution_count >= self._solution_limit:
            self.StopSearch()

    def solution_count(self):
        return self._solution_count
