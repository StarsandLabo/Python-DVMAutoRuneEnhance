class ClickCondition():
    dynamicid = 0
    
    OpenListMenu = {
        "template"  : "resources/img/template/other/openListmenu.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'OpenListMenu',
        "GETCAPTURE": False
    }; dynamicid += 1
    
    EnterRuneManagement = {
        "template"  : "resources/img/template/other/enterRuneManagement.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'EnterRuneManagement',
        "GETCAPTURE": False
    }; dynamicid += 1
    
    EnterRuneList = {
        "template"  : "resources/img/template/management/management.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'EnterRuneList',
        "GETCAPTURE": False
    }; dynamicid += 1
    
    def RarerityCheck(rarerity: str, confidence=0.8):
        import pyautogui as pag
        import sys
        if rarerity.upper() not in ['LEGEND', 'HERO', 'RARE', 'COMMON']:
            pag.alert   (   
                text      = f'Rarerity specify in LEGEND, HERO, RARE, COMMON. (You choose {rarerity})',
                title     = 'Value error',
                button    = ('OK')
            )
            sys.exit()
        if confidence > 1 or confidence < 0:
            pag.alert   (   
                text      = r'The value that can be entered is exceeded. (Between 0 and 1)',
                title     = 'Value error',
                button    = ('OK')
            )
            sys.exit()
        arr = {
            "template"  : f"resources/img/template/enhance/rarerity_{rarerity.lower()}.png",
            "timeoutsec": 1,
            "maxtry"    : 3,
            "scene"     : f'RarerityCheck_{rarerity.upper()}',
            "confidence": confidence,
            "GETCAPTURE": False
        }
        return arr

    # 旧レアリティ判別版
    """
    def TargetLevelSelect(magicNumber, confidence=0.8):
        import pyautogui as pag
        import sys
        if magicNumber not in [3, 6, 9, 12]:
            pag.alert   (   
                text      = f'magicNumber specify in 3, 6, 9, 12. (You choose {magicNumber})',
                title     = 'Value error',
                button    = ('OK')
            )
            sys.exit()
        if confidence > 1 or confidence < 0:
            pag.alert   (   
                text      = r'The value that can be entered is exceeded. (Between 0 and 1)',
                title     = 'Value error',
                button    = ('OK')
            )
            sys.exit()
        arr = {
            "template"  : f"resources/img/template/enhance/to{magicNumber}.png",
            "timeoutsec": 1,
            "maxtry"    : 3,
            "scene"     : f'TargetLevelSelect',
            "confidence": confidence,
            "GETCAPTURE": False
        }
        return arr
    """
    def TargetLevelSelect(rarerity, confidence=0.8):
        import pyautogui as pag
        import sys
        
        MagicNumberTable = {
            'LEGEND': 12,
            'HERO': 9,
            'RARE': 6,
            'COMMON': 3
        }
        
        if rarerity not in ['LEGEND', 'HERO', 'RARE', 'COMMON']:
            pag.alert   (   
                text      = f'rarerity specify in LEGEND, HERO, RARE, COMMON (You choose {rarerity})',
                title     = 'Value error',
                button    = ('OK')
            )
            sys.exit()
        if confidence > 1 or confidence < 0:
            pag.alert   (   
                text      = r'The value that can be entered is exceeded. (Between 0 and 1)',
                title     = 'Value error',
                button    = ('OK')
            )
            sys.exit()
        arr = {
            "template"  : f"resources/img/template/enhance/to{MagicNumberTable[rarerity.upper()]}.png",
            "timeoutsec": 1,
            "maxtry"    : 3,
            "scene"     : f'TargetLevelSelect',
            "confidence": confidence,
            "GETCAPTURE": False
        }
        return arr

    def Position(number, confidence, dynamicid=dynamicid):
        import pyautogui as pag
        import sys
        if number > 6 or number < 1:
            pag.alert   (   
                text      = r'The value that can be entered is exceeded. (Between 1 and 6)',
                title     = 'Value error',
                button    = ('OK')
            )
            sys.exit()
        if confidence > 1 or confidence < 0:
            pag.alert   (   
                text      = r'The value that can be entered is exceeded. (Between 0 and 1)',
                title     = 'Value error',
                button    = ('OK')
            )
            sys.exit()
        arr = {
            "template"  : f"resources/img/template/runelist/pos{number}s.png",
            "timeoutsec": 1,
            "maxtry"    : 3,
            "scene"     : f'EquipPosition_{number}',
            "confidence": confidence,
            "GETCAPTURE": False
        }; dynamicid += 1
        return arr
    
    Ascend = {
        "template"  : "resources/img/template/runelist/toAscend.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'Ascend',
        "GETCAPTURE": False
    }; dynamicid += 1

    OpenSortMenu = {
        "template"  : "resources/img/template/runelist/sort.png",
        "timeoutsec": 0.75,
        "maxtry"    : 4,
        "scene"     : 'OpenSortMenu',
        "GETCAPTURE": False
    }; dynamicid += 1

    EnhanceInSortMenu = {
        "template"  : "resources/img/template/runelist/enhance.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'EnhanceInSortMenu',
        "GETCAPTURE": False
    }; dynamicid += 1

    EnterEnhance = {
        "template"  : "resources/img/template/runelist/toEnhance.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'EnterEnhance',
        "GETCAPTURE": False
    }; dynamicid += 1
    
    RepeatCheck = {
        "template"  : "resources/img/template/enhance/repeat.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'RepeatCheck',
        "GETCAPTURE": False
    }; dynamicid += 1
    SetCommonEnhance = {
        "template"  : "resources/img/template/enhance/commonEnhance.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'SetCommonEnhance',
        "GETCAPTURE": False
    }; dynamicid += 1
    StartEnhance = {
        "template"  : "resources/img/template/enhance/startEnhance.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'StartEnhance',
        "GETCAPTURE": False
    }; dynamicid += 1
    ReturnLuneList = {
        "template"  : "resources/img/template/enhance/back.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'ReturnRuneList',
        "GETCAPTURE": False
    }; dynamicid += 1
    SerachLockAndSell = {
        "template"  : "resources/img/template/runelist/lockAndSell.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'SearchLockAndSell',
        "GETCAPTURE": False
    }; dynamicid += 1
    GetSummaryHeight = {
        "template"  : "resources/img/template/runelist/summaryH.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'GetSummaryHeight',
        "GETCAPTURE": False
    }; dynamicid += 1
    GetSummaryWidth = {
        "template"  : "resources/img/template/runelist/summaryW.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'GetSummaryWidth',
        "GETCAPTURE": False
    }; dynamicid += 1
    GetSummarySpace = {
        "template"  : "resources/img/template/runelist/summarySpace.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'GetSummarySpace',
        "GETCAPTURE": False
    }; dynamicid += 1

    RarerityCheck_DIA = {
        "template"  : "resources/img/template/enhance/rarerityCheckDia.png",
        "timeoutsec": 1,
        "maxtry"    : 3,
        "scene"     : 'EnterRuneList',
        "GETCAPTURE": False
    }; dynamicid += 1