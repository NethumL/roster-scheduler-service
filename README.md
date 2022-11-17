# Service for Constraint Based Roster Scheduler

Service to generate schedule for Constraint Based Roster Scheduler

## Running

- Get the required Python packages

```shell
$ pip install -r requirements.txt
```

- Set the required environment variables (see [environment variables section](#environment-variables) for details)

- Start server

```shell
$ gunicorn app:app
```

## Environment variables

### `SECRET`

- Shared secret between this service and the roster scheduler webapp
- Needs to be a sufficiently long random string, eg: `DSAVDF+BTMgoBszC9zUJwHx1/s4Gc2ebz9oG1VjrBB8=`
- Can use the OpenSSL command line tool to generate one

```shell
$ openssl rand -base64 32
DSAVDF+BTMgoBszC9zUJwHx1/s4Gc2ebz9oG1VjrBB8=
```

### `RESPONSE_ENDPOINT`

- API endpoint where the generated roster will be sent
- If the roster scheduler webapp is hosted at https://example.com, then the `RESPONSE_ENDPOINT` should be https://example.com/api/roster/generate/save
