# FMRSD sheets

Timesheet, trip timesheet and fuel sheet, served from **meercat** to every device on the tailnet.

- `timesheets.html`: the forms
- `server.py`: serves the page and saves entries (Python 3, nothing to install)
- `data/store.json`: all your entries. `data/store-YYYYMMDD.json` is a copy kept each day before the first change.
- `install.sh`: sets up the service on meercat

## Install (once)

From Gram, copy the folder to meercat:

    scp -r fmrsd-sheets meercat:~/

Then log in to meercat and run the installer:

    ssh meercat
    cd ~/fmrsd-sheets
    bash install.sh

The last thing it prints is the address, something like `https://meercat.your-tailnet.ts.net`.
Open it on any device and bookmark it (or "Add to Home Screen" on a phone).

## If `tailscale serve` fails

HTTPS may not be turned on for your tailnet. Either turn it on at
https://login.tailscale.com/admin/dns (enable MagicDNS and HTTPS Certificates) and rerun
`bash install.sh`, or have the server listen on the Tailscale address instead:

    sed -i 's/--host 127.0.0.1/--host '"$(tailscale ip -4)"'/' ~/.config/systemd/user/fmrsd-sheets.service
    systemctl --user daemon-reload && systemctl --user restart fmrsd-sheets

and open `http://meercat:8077`.

## Everyday

- Entries save to meercat as you type. The toolbar shows **Saved**; a red banner means meercat can't be reached.
- Switching back to the tab picks up changes made on another device.
- Print with the toolbar buttons; choose your network printer in the print dialog.

## Updating the page

Copy a new `timesheets.html` over the old one. No restart needed. Your entries are untouched.

## Handy commands (on meercat)

    systemctl --user status fmrsd-sheets     # is it running?
    journalctl --user -u fmrsd-sheets -n 50  # recent log
    systemctl --user restart fmrsd-sheets
