class AlertMessageBuilder:
    # Main entry point to build alert messages.
    # Returns a message string comprised of a rocket alert header
    # and alert location list 
    def buildAlerts(self, eventData):
        alerts = eventData["alerts"]

        if not isinstance(alerts, (list)):
            alerts = [alerts]

        alertList = self.__buildAlertList(alerts)

        alertTypeId = eventData["alertTypeId"]
        if (alertTypeId == 1):
            header = "Rocket alert"
        elif (alertTypeId == 2):
            header = "Hostile UAV alert"
        else:
            header = "Red alert"
        header += f" {alerts[0]['timeStamp']}:"
        return f"{header}\n\n" \
                f"{alertList}\n\n"

    # Returns a list of alert locations, each of which in a new line
    def __buildAlertList(self, alerts):
        text = ""
        for alert in alerts:
            alertText = self.__buildAlert(alert)
            if text:
                text = f"{text}\n"
            text = f"{text}{alertText}"
        return text

    # Given an alert, returns a string in format "locationName (areaName)"
    def __buildAlert(self, alert):
        areaNameHe = alert["areaNameHe"]
        areaNameEnglish = alert["areaNameEn"]
        locationNameHe = alert["name"]
        locationNameEnglish = alert["englishName"]

        name = locationNameEnglish or locationNameHe
        areaName = areaNameEnglish or areaNameHe
        
        if areaName is None:
            return name
        return f"{name} ({areaName})"    
        