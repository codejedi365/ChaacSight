#﻿ ---------------------------------------------------
# Script: SuspendPowerPlan.ps1
# Author: codejedi365
# Version: 0.2
# Date: 11/13/2019 23:04:09
# Original Script: https://github.com/stefanstranger/PowerShell/blob/master/Examples/SuspendPowerPlan.ps1
# Original Author: Stefan Stranger
# Original Date: 07/05/2014 15:01:57
# Description: Helper Function to Suspend Power Plan while doing other things
# ---------------------------------------------------

<#
.Synopsis
   Function to suspend your current Power Plan settings indefinitely while script is running
.DESCRIPTION
   Function to suspend your current Power Plan settings indefinitely while script is running.
   Scenario: When running an external long scripted task use PowerShell script execution to prevent
   your PC from going into sleep mode.
.EXAMPLE
   Suspend-PowerPlan -option System
   Start infinitely running script that prevents sleep idle timeout while running
   Suspend-PowerPlan -Verbose
   Start script with verbose output.  Optionally add an option command as well
#>
function Suspend-Powerplan
{
   [CmdletBinding()]
   [Alias()]
   [OutputType([int])]
   Param
   (
        # Param1 help description
        [ValidateSet("Away","Display","System")]
        [string]$option
         
   )

   $code=@' 
[DllImport("kernel32.dll", CharSet = CharSet.Auto,SetLastError = true)]
  public static extern void SetThreadExecutionState(uint esFlags);
'@

   $ste = Add-Type -memberDefinition $code -name System -namespace Win32 -passThru 
   $ES_CONTINUOUS = [uint32]"0x80000000" #Requests that the other EXECUTION_STATE flags set remain in effect until SetThreadExecutionState is called again with the ES_CONTINUOUS flag set and one of the other EXECUTION_STATE flags cleared.
   $ES_AWAYMODE_REQUIRED = [uint32]"0x00000040" #Requests Away Mode to be enabled.
   $ES_DISPLAY_REQUIRED = [uint32]"0x00000002" #Requests display availability (display idle timeout is prevented).
   $ES_SYSTEM_REQUIRED = [uint32]"0x00000001" #Requests system availability (sleep idle timeout is prevented).

   Switch ($option)
   {
      "Away" {$setting = $ES_AWAYMODE_REQUIRED}
      "Display" {$setting = $ES_DISPLAY_REQUIRED}
      "System" {$setting = $ES_SYSTEM_REQUIRED}
      Default {$setting = $ES_SYSTEM_REQUIRED}
   }

   Write-Verbose "Power Plan suspended with option: $option"
   $ste::SetThreadExecutionState($ES_CONTINUOUS -bor $setting)

   try
   {
      # Write-Verbose "Exercising forever..."
      while(1) {
         start-sleep -seconds 600
      }
   }

   finally
   {
    Write-Verbose "Power Plan suspension ended"
    $ste::SetThreadExecutionState($ES_CONTINUOUS)
   }

}
