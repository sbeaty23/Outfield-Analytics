# Data sources

## MLB Stats API

The MLB Stats API supplies current-season baseball information only. Outfield
Analytics uses it for active teams and rosters, current team and player
statistics, standings, and narrow current/upcoming schedule windows.

The provider is not used for historical bulk datasets, model training, live
game feeds, images, logos, or other media. Responses are normalized into
Outfield Analytics schemas before they reach services, routes, or the frontend.

Historical data will be sourced separately in a later phase.

Coaching staff is deferred: the upstream coaching endpoint has not been
validated for this phase and is not a completion requirement.

Missing optional statistics and last-ten records are null. A valid empty
statistics response has `stats: null`; it does not mean zero performance.
Innings are preserved as baseball strings, never decimal innings.
