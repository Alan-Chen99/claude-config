# `warden`

```
bin/warden list
bin/warden check
```

- `list` — one line per service: `<name>\t<owner>\t<state>`.
- `check` — one line for each service that is not up, then a summary line
  counting them. Exit status 1 when any service is down, 0 otherwise.
