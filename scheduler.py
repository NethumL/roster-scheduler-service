import random

from ortools.sat.python import cp_model


class Scheduler:
    def get_schedule(self):
        data = {
            "doctors": {},
            "constraints": {
                "minDoctors": [10 for _ in range(3)],
                "maxDoctors": [15 for _ in range(3)],
            },
        }

        num_shifts = 3
        num_days = 30
        num_doctors = 50
        leave_days = 2

        for i in range(1, num_doctors + 1):
            prefs = [0, 1, 2]
            leaves = set(map(lambda _: random.randint(0, 9), range(leave_days)))
            random.shuffle(prefs)
            data["doctors"][f"d{i}"] = {"prefs": prefs, "leaves": leaves}

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
                num_doctors: list[cp_model.IntVar] = []
                for doctor, props in data["doctors"].items():
                    prefs: list[int] = props["prefs"]
                    leaves: list[int] = props["leaves"]
                    if day not in leaves:
                        num_doctors.append(shifts[(doctor, day, shift)])
                model.Add(min_doctors <= sum(num_doctors))
                model.Add(max_doctors >= sum(num_doctors))

        solver = cp_model.CpSolver()
        solver.parameters.linearization_level = 0
        solver.parameters.enumerate_all_solutions = True

        class PartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
            def __init__(self, shifts, limit):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self._shifts = shifts
                self._solution_count = 0
                self._solution_limit = limit

            def OnSolutionCallback(self):
                self._solution_count += 1
                print("Solution %i" % self._solution_count)

                for doctor, props in data["doctors"].items():
                    prefs: list[int] = props["prefs"]
                    leaves: set[int] = props["leaves"]
                    days = all_days.difference(leaves)
                    for day in days:
                        is_working = False
                        for s in prefs:
                            if self.Value(self._shifts[(doctor, day, s)]):
                                is_working = True
                                print(
                                    f"\tDoctor {doctor} works shift {s}/{prefs[0]}"
                                    + f" on {day}"
                                )
                        if not is_working:
                            print(f"\tDoctor {doctor} does not work on {day}")

                if self._solution_count >= self._solution_limit:
                    self.StopSearch()

            def solution_count(self):
                return self._solution_count

        solution_limit = 1
        solution_printer = PartialSolutionPrinter(shifts, solution_limit)

        solver.Solve(model, solution_printer)

        # Statistics
        print("\nStatistics")
        print("  - conflicts      : %i" % solver.NumConflicts())
        print("  - branches       : %i" % solver.NumBranches())
        print("  - wall time      : %f s" % solver.WallTime())
        print("  - solutions found: %i" % solution_printer.solution_count())
        return {
            "conflicts": solver.NumConflicts(),
            "branches": solver.NumBranches(),
            "wall_time": solver.WallTime(),
            "solution_count": solution_printer.solution_count(),
        }
