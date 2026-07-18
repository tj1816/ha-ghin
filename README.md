# GHIN Golf Handicap for Home Assistant

A custom Home Assistant integration that pulls your USGA GHIN handicap index, low handicap index, scoring average, and most recent round directly into Home Assistant as sensors.

This uses GHIN's own (unofficial, undocumented) API - the same one ghin.com's website calls - so there's no official developer key. Setup requires grabbing one static token out of your browser once (see below).

## Sensors created

- `sensor.ghin_<club>_handicap_index` - current Handicap Index
- `sensor.ghin_<club>_low_hi` - Low HI (lowest handicap in the last 12 months)
- `sensor.ghin_<club>_last_round_score` - most recent posted round, with attributes for course, tees, net score, differential, course/slope rating, and status
- `sensor.ghin_<club>_scoring_average` - scoring average, with attributes for lowest/highest score and total rounds posted

## Installation

### Via HACS (recommended)

1. In HACS, go to the three-dot menu → **Custom repositories**
2. Add this repo URL, category **Integration**
3. Search for "GHIN Golf Handicap" in HACS and install
4. Restart Home Assistant

### Manual

1. Copy `custom_components/ghin` into your Home Assistant `config/custom_components/` folder
2. Restart Home Assistant

## Setup

Go to **Settings → Devices & Services → Add Integration → GHIN Golf Handicap**.

You'll need three things:

- **Email** - the email you use to log into ghin.com
- **Password** - your ghin.com password
- **Client token** - a static token GHIN's website sends along with every login (see below)

### Finding your client token

GHIN's web client includes a static token with each login request. It identifies the request as coming from the official web app rather than any specific account, but GHIN doesn't publish it anywhere, so you have to capture it yourself once:

1. Open [ghin.com](https://www.ghin.com) in a desktop browser
2. Open DevTools (F12 or right-click → Inspect) and go to the **Network** tab
3. Log in normally on the page
4. In the Network tab, find the request to `golfer_login.json`
5. Click it, open the **Request Payload** (or **Payload**) section, and copy the value of the `token` field
6. Paste that into the integration's setup form

If GHIN ever rotates this token and your sensors stop updating (auth errors in the logs), go to the integration in **Settings → Devices & Services**, click it, and choose **Reconfigure** to enter the new token without losing your entity IDs or history.

## Update frequency

Data refreshes every 6 hours by default. You can change this from the integration's **Configure** options (1-24 hours).

## Disclaimer

This is an unofficial, community-built integration. It is not affiliated with or endorsed by the USGA or GHIN. It relies on an undocumented API that could change or break at any time without notice.

## Contributing

PRs welcome. This started as a personal dashboard project, so there's plenty of room for improvement (additional sensors, better error handling, tests, etc).

## License

MIT - see [LICENSE](LICENSE).
