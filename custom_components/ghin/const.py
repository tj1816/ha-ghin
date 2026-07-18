"""Constants for the GHIN integration."""

DOMAIN = "ghin"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_CLIENT_TOKEN = "client_token"

DEFAULT_SCAN_INTERVAL_HOURS = 6

LOGIN_URL = "https://api2.ghin.com/api/v1/golfer_login.json"
SCORES_URL = "https://api2.ghin.com/api/v1/scores.json"

# GHIN's own web client sends a static token alongside login credentials.
# It identifies the request as coming from the official web client and is
# not tied to any individual account, but it isn't published anywhere -
# each user must capture their own via browser DevTools on a fresh login
# (Network tab -> golfer_login.json -> Request Payload -> "token" field)
# and enter it during setup. If GHIN ever rotates the token, users can
# update it via the integration's Reconfigure option.
GHIN_SOURCE = "GHINcom"

ATTR_LOW_HI = "low_hi_display"
ATTR_CLUB_NAME = "club_name"
ATTR_REVISION_DATE = "rev_date"
