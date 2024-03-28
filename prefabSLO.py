import json
import os
import requests

# Define environment for API calls eg. https://xxxx.live.dynatrace.com
dt_env = ""

# Defining required functions
def getDisplayName():
  defaultName = svcoff_tag
  while True:
    displayName = input(f"Set a prefix for the display name of the SLOs, without special characters. Default: {svcoff_tag} \n")
    if displayName.strip() == "":
        displayName = defaultName
    yn = input(f"SLOs will be displayed in the form \"{displayName} availability\", \"{displayName} performance\"...\nIs this OK? (y/n) ")
    if yn.lower() == "y" or yn.lower() == "yes":
      return displayName.strip()

# Get user input
token = os.environ['DT_ACCESS_TOKEN']
svcoff_tag = input("Paste in the tag you'd like to generate SLOs for (key:value): ")
displayName = getDisplayName()
filter = f"tag(\"{svcoff_tag}\")"


# Establish header for API calls
headers = {"Authorization":f"Api-Token {token}"}

# Format a metricName from displayName
metricName = displayName.replace(" ", "_").lower()

# Store metric & SLO location data to build dashboard
metricData = {}
locationData = {}

# Iterate over files in the templates folder
for filename in os.listdir("SLOTemplates"):
  # Check if the file is a JSON file
  if filename.endswith(".json"):
    # Construct the full file path
    file_path = os.path.join("SLOTemplates", filename)
    
    # Open the file in read mode
    with open(file_path, "r") as f:
      # Load the JSON data
      data = json.load(f) 

      # Apply filter
      data["filter"] += filter

      # Apply displayName
      data["name"] = displayName + data["name"]

      # Apply metricName
      data["metricName"] = metricName + data["metricName"]

      # Post the data to Dynatrace
      post = requests.post(f"{dt_env}/api/v2/slo", headers=headers, json=data)

      # Print response
      print(post.content)
      print(post)

      # Gather metric data and SLO locations
      response = post.headers
      metricData[filename] = "func:slo." + data["metricName"]
      locationData[filename] = response.get("location")

# Create overall SLO 
with open("SLOOverallTemplate.json", "r") as f:
  metric = "("
  for key in metricData:
    metric += metricData[key] + " + "
  metric = metric[0:-3] + ") / 4"
  data = json.load(f)
  data["metricExpression"] = metric 

  # Apply displayName
  data["name"] = displayName + data["name"]

  # Apply metricName
  data["metricName"] = metricName + data["metricName"]

  # Post the data to Dynatrace
  post = requests.post(f"{dt_env}/api/v2/slo", headers=headers, json=data)

  # Print response
  print(post.content)
  print(post)

  # Gather metric data and SLO locations
  response = post.headers
  metricData["SLOOverallTemplate.json"] = "func:slo." + data["metricName"]
  locationData["SLOOverallTemplate.json"] = response.get("location")


# Update dashboard JSON template placeholders
with open("DashboardTemplates/DashboardTemplate.json", "r") as f:
  data = f.read()
  data = data.replace("[Display Name]", f"{displayName} SLO Dashboard")
  data = data.replace("[Service Level Availability]", locationData["SLOAvailabilityTemplate.json"])
  data = data.replace("[Service Level Availability Metric]", metricData["SLOAvailabilityTemplate.json"])
  data = data.replace("[Service Performance]", locationData["SLOPerformanceTemplate.json"])
  data = data.replace("[Service Performance Metric]", metricData["SLOPerformanceTemplate.json"])
  data = data.replace("[User Experience]", locationData["SLOUXTemplate.json"])
  data = data.replace("[User Experience Metric]", metricData["SLOUXTemplate.json"])
  data = data.replace("[Synthetic Availability]", locationData["SLOSyntheticAvailabilityTemplate.json"])
  data = data.replace("[Synthetic Availability Metric]", metricData["SLOSyntheticAvailabilityTemplate.json"])
  data = data.replace("[Overall Performance]", locationData["SLOOverallTemplate.json"])
  data = data.replace("[Overall Performance Metric]", metricData["SLOOverallTemplate.json"])

  # Save filled template to file
  filledTemplate = json.loads(data)
  with open(f"FilledTemplates/{displayName} SLO Dashboard.json", "w") as f:
    json.dump(filledTemplate, f)
  
  # Post dashboard to tenant
  post = requests.post(f"{dt_env}/api/config/v1/dashboards", headers=headers, json=filledTemplate)
  print(post.content)
  print(post)    






