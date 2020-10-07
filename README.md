# lighthouse-api
API for generating lightouse reports

## Usage

To generate a lighthouse report (html + json), and automatically upload it to
an Azure blob storage send a POST with content-type: application/json to the root
of the application.

The JSON body should contain the following attributes:
* application = The name of the application
* commit = The commit hash that generated the change in code
* environment = The environment (active/stage)
* team = The responsible team (withhout the #)
* urls = A JSON array of urls to scan

Optional attributes:
* callback = A url to call when the report is finished and uploaded

Filenames are on the format [application]\_[commit]_[url-path].[json|html]

## Example

`curl -XPOST --data '{"application":"test", "team":"team-pipeline", "commit":"123567", "environment":"test", "urls":["https://www.kth.se"], "callback":"https://www.kth.se"}' --header "Content-type: application/json" api.kth.se/api/lighthouse `