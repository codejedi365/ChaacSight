##
 # Event Handler Registration
##

registration_tree = {}
def registerEventHandler( evt_type, handler_name ):
	if evt_type not in registration_tree:
		registration_tree[evt_type] = []
	registration_tree[evt_type].append(handler_name)


## Event Handlers for Data Wrangling
registerEventHandler("EVENT_TYPE_NEW_DATA", "DataWrangling")  # Handles DataFrame, additional months etc

## Event Handlers for Exogenous Variable model improvements
registerEventHandler("EVENT_TYPE_TGTLOC_FOUND", "EvaluateModelMAE")   # keymae
registerEventHandler("EVENT_TYPE_TGTLOC_FOUND", "FindExogLocations")  #
registerEventHandler("EVENT_TYPE_EXOGLOC_FOUND", "ComboCreation")
registerEventHandler("EVENT_TYPE_EXOG_COMBO_FOUND", "EvaluateModelMAE")  # exmae
registerEventHandler("EVENT_TYPE_EXMAE_CALCULATED", "ComboCreation")     # find next layer combo if exists
registerEventHandler("EVENT_TYPE_TGTLOC_IMPROVED", "EvaluateModelMAE")   # Post better exmae, set current model mae

## Event Handlers for Prediction creation
registerEventHandler("EVENT_TYPE_TGTLOC_FOUND", "FuturePredictions")
registerEventHandler("EVENT_TYPE_TGTLOC_IMPROVED", "FuturePredictions")
registerEventHandler("EVENT_TYPE_TGTLOC_PREDICTED", "UpdateHeatmap")
registerEventHandler("EVENT_TYPE_TGTLOC_PREDICTED", "UpdateDependentPredictions")

## Event Handlers for System Tasks
registerEventHandler("EVENT_TYPE_TIMER", "NewMonth")
registerEventHandler("EVENT_TYPE_TIMER", "ReEvaluation")
registerEventHandler("EVENT_TYPE_TIMER", "Backups")
registerEventHandler("EVENT_TYPE_TIMER", "Maintenance")

## Event Handlers for User Interaction
registerEventHandler("EVENT_TYPE_SYSTEM_QUIT", "Shutdown")
