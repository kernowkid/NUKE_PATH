## autosavePath expression to copy and paste into nuke prefs

[if {[value root.name] !=""} {return  [file mkdir c:/Users/Admin/AppData/Local/nuke/autosaves/[lindex [split [value root.name] "/ "] 3 ]]c:/Users/Admin/AppData/Local/nuke/autosaves/[lindex [split [value root.name] "/"] 3]/[file tail [value root.name].autosave]} {return [firstof [value root.name] [getenv NUKE_TEMP_DIR]/].autosave}] 