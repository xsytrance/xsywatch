# WFF official validator evidence — engine outputs

```
$ tools/wff_validate.sh 4 watchfaces/aurelius/app/src/main/res/raw/watchface.xml
INFO: WFF Validation Application Version 1.0. Maximum Supported Format Version #5
INFO: ✅  PASSED : watchfaces/aurelius/app/src/main/res/raw/watchface.xml is valid against watch face format version #4

$ tools/wff_validate.sh 4 <generated fixture_analog.xml>
INFO: WFF Validation Application Version 1.0. Maximum Supported Format Version #5
INFO: ✅  PASSED : /tmp/claude-1000/-home-xsyprime-xsywatch/030d59e9-9dd1-4b68-a769-b311cfcd8cfe/scratchpad/fixture_analog.xml is valid against watch face format version #4

$ tools/wff_validate.sh 4 <generated fixture_digital.xml>
INFO: WFF Validation Application Version 1.0. Maximum Supported Format Version #5
INFO: ✅  PASSED : /tmp/claude-1000/-home-xsyprime-xsywatch/030d59e9-9dd1-4b68-a769-b311cfcd8cfe/scratchpad/fixture_digital.xml is valid against watch face format version #4
```
