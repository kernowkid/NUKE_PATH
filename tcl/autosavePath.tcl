## autosavePath expression to copy and paste into nuke prefs

[ if {[value root.name] !=""} {return  [file mkdir  [getenv NUKE_TEMP_DIR]/[lindex [split [value root.name] "/ "] 2 ]][getenv NUKE_TEMP_DIR]/[lindex [split [value root.name] "/"] 2]/[file tail [value root.name].autosave]} {return [firstof [value root.name] [getenv NUKE_TEMP_DIR]/].autosave} ]

orig:
[firstof [value root.name] [getenv NUKE_TEMP_DIR]/].autosave