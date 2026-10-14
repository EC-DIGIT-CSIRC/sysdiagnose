# iOS 27 `logs/ContainerManager/state.json`

New in the iOS 27 sysdiagnose. It replaces the text logs older releases carried for the container
manager (`logs/MobileContainerManager/containermanagerd.log*`) and the app installer
(`logs/appinstallation/*`), which are not present in iOS 27 archives. The existing SAF
`containermanager` / `appinstallation` parsers and the iLEAPP `mobileContainerManager` module therefore
return nothing on iOS 27. This parser reads the JSON instead.

Observed on one iPhone, iOS 27.0 build 24A437 (file 3.98 MB). Facts are what the file shows. Inferences are
marked and are not proven by this file alone. Synthetic data only is shipped with the code.

## Structure (fact)

Root object with two scopes: `"<system>"` (system containers) and a user id string (`"501"`, user `mobile`).
Each scope holds:

| key | content |
|---|---|
| `containers` | `{group: {identifier: record}}`. Group = `<kind>-<persona>[-T]` (`-T` = transient) |
| `containerClassPaths` | class number -> on-disk class directory, per persona (path, staging, transient tables) |
| `clientCache.mru` | recent client processes of the container manager daemon (29 per scope) |
| `personas` | persona identities and managed paths |
| `codesignCache.orderedEntries` | user scope only: ordered cache of code-signing registrations (1799) |
| `childParentMap` | user scope only: extension identifier -> host app identifier (637) |

Container groups and counts in the sample: `app-33` 153 (system program bundles), `protectedSystem-0` 5,
`systemData-0` 33, `systemGroup-0` 42, `appData-501` 371, `appGroup-501` 272, `daemon-501` 32,
`pluginData-501` 1249 (extensions), `perUserApp-501` 0, transient groups 0. Total 2157 container records.

Container record keys (always the same eight): `uuid`, `pathIdentifier`, `generation`, `schemaVersion`,
`posixOwnership`, `corrupt`, `ignore`, `node`. `node` is `null` or an object with `birthtime`, `ctime`,
`mtime`, `lastSeen`: ISO-8601 UTC strings with milliseconds and `Z`.

Class numbers (from `containerClassPaths`): 1 Bundle/Application, 2 Data/Application, 3 Bundle/PluginKitPlugin,
4 Data/PluginKitPlugin, 5 Bundle/VPNPlugin, 7 Shared/AppGroup, 8 Bundle/Framework, 10 Data/InternalDaemon,
12 Data/System, 13 Shared/SystemGroup, 14 Bundle/Application (per user), 15 Data/ProtectedSystem.

## Measured relationships (fact)

* `pathIdentifier` is the container directory name. It appears in `logs/MobileInstallation/mobile_installation.log*`
  ("Data container for ... is now at .../Data/Application/<pathIdentifier>") and in spindump. `uuid` is a
  different UUID for every record and appears nowhere else in the archive text. No `pathIdentifier` repeats.
* `node` is `null` for 419 of 2157 records (19%). In exactly those records `generation` is `-1`; every
  record with a node has `generation` >= 1000.
* In all 1738 records with a node: `birthtime <= ctime`, `mtime <= ctime`, `ctime <= lastSeen`. `lastSeen` falls
  within one hour on the capture day (1576 distinct values); birth times span the device's life.
* All 609 `pluginData` containers that have a parent in `childParentMap` have an `appData` parent present.
* Of 188 `pathIdentifier` values that the installer log also names, 113 line hits point at records with
  `node: null` (the installer log names directories that no longer exist as nodes).
* iOS 27 still carries `logs/MobileInstallation/mobile_installation.log*`. The iOS 26.6 (23G71) sample used for
  comparison has no `MobileContainerManager`, `ContainerManager` or `appinstallation` folder (only
  `MobileInstallation`), so the old container-manager text log could not be compared line by line.

## Meaning (inference, not proven by this file)

* `birthtime` of an app data container approximates when the device first created the container (first install,
  or re-creation after restore). It is not proof of who installed the app or when the user opened it.
* `node: null` means the daemon keeps a record for a container directory that did not exist at capture time:
  removed, replaced by a new directory, or not yet created. This file cannot tell these apart.
* `lastSeen` looks like the daemon's last check of the directory, not user activity.
* `generation` values (1000, 1001, 1005-1008) are kept raw; their meaning is not established.

## Rows produced

One row per record, stable columns, a `record_type`: `container`, `codesign`, `child_parent`, `client`,
`class_path`, `persona`, `managed_path`, `unknown_section`. Row counts per type equal the file's record counts.
Unknown keys are kept as JSON text in `other`; problems are noted in `notes` and warned, never raised.
Timestamps are UTC; a bad, out-of-range or non-ISO value yields an empty time and a note, never a made-up date.
Integers outside 64 bits are kept as text. Entitlement values are not copied (only their count).

## Limits

Tested on iOS 27.0 (24A437) only. A match is a lead: an empty result does not prove an app was never present,
because the file is a snapshot of daemon state and records can be absent for reasons outside this file.
