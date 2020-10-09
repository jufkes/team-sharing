import time
from googleapiclient import discovery as gce_discovery, errors as gce_errors
from oauth2client.client import GoogleCredentials
from google.oauth2 import service_account
import webbrowser
import requests
import json

def main():

    credentials = service_account.Credentials.from_service_account_file(filename='test.json')

    def create_project(project_id):
        service = gce_discovery.build('cloudresourcemanager', 'v1', credentials=credentials)
        project_body = {
            "name": "External Customer Project3",
            "parent": {
                "id": "111111111111",
                "type": "folder"
            },
            "projectId": project_id
        }

        try:
            request = service.projects().create(body=project_body)
            request.execute()
            project_finished_creating = False
            while not project_finished_creating:
                request = service.projects().get(projectId=project_id)
                try:
                    new_project = request.execute()
                    project_finished_creating = True
                except Exception as e:
                    time.sleep(2)
                    print("Failed to get created project")
            print(new_project)
        except Exception as e:
            print("Failed creating the project")
            print(e)

    def add_sub_billing_account(project_id, billing_id):
        service = gce_discovery.build('cloudbilling', 'v1', credentials=credentials)
        name = "projects/" + project_id
        billingAccountName = "billingAccounts/" + billing_id
        payload = {
            "projectId": project_id,
            "billingAccountName": billingAccountName,
            "billingEnabled": True,
            "name": name
        }

        try:
            request = service.projects().updateBillingInfo(name=name, body=payload)
            request.execute()
        except Exception as e:
            print(e)


    def post_to_billing_account_service(provider_id, provider_alias, gcp_project_id, sub_billing_account_id, billing_account_number, aip):
        url = 'http://to_be_determined/at/a/later/date'
        updated = False
        payload = {
            "providerId": provider_id,
            "providerAlias": provider_alias,
            "gcpProjectId": gcp_project_id,
            "subBillingAccountId": sub_billing_account_id,
            "billingAccountNumber": billing_account_number,
            "AIP": aip
        }
        while not updated:
            try:
                r = requests.post(url, data=payload)
                updated = True
            except Exception as e:
                time.sleep(2)
                print("Account service update failed...retrying")
        print("Account service updated for provider alias: {0} sub_billing_id: {1} api: {2} ").format(provider_alias, sub_billing_account_id, aip)


    def open_console(project_id):
        url = 'https://console.cloud.google.com/home/dashboard?folder=&organizationId=&project={0}'.format(project_id)
        print(url)
        webbrowser.open_new_tab(url)

    def add_permanent_iam_permissions(project_id, role, user):
        service = gce_discovery.build('cloudresourcemanager', 'v1', credentials=credentials)

        role = "roles/" + role
        member = "user:" + user
        policy_get = get_iam_policy(project_id)

        binding = None
        for b in policy_get["bindings"]:
            if b["role"] == role:
                binding = b
                break
        if binding is not None:
            binding["members"].append(member)
        else:
            binding = { "role": role, "members": [member] }
            policy_get["bindings"].append(binding)

        policy_update = policy = (
            service.projects()
                .setIamPolicy(resource=project_id, body={"policy": policy_get})
                .execute()
        )

        print policy_update

    def get_iam_policy(project_id):
        service = gce_discovery.build('cloudresourcemanager', 'v1', credentials=credentials)
        policy = (
            service.projects()
                .getIamPolicy(
                resource=project_id,
                body={"options": {"requestedPolicyVersion": 3}},
            )
                .execute()
        )
        return (policy)

    def temporary_iam_permissions(project_id, role, user, length_in_hours):
        from datetime import datetime, timedelta
        from googleapiclient.errors import HttpError

        service = gce_discovery.build('cloudresourcemanager', 'v1', credentials=credentials)

        role = "roles/" + role
        member = "user:" + user

        policy_get = get_iam_policy(project_id)

        # setting the title, description and end time in hours -- this could be updated to define X number of hours
        title = "Expires_in_1_hour"
        description = "Permission granted for 1 hour"
        end_time = datetime.utcnow() + timedelta(hours=length_in_hours)

        # set the endstate expression
        expression = "request.time < timestamp('" + str(end_time.isoformat()[:-3]+'Z') + "')"

        # build the condition definition
        condition = {
            "title": title,
            "description": description,
            "expression":
                expression
        }

        binding = { "role": role, "members": [member], "condition": condition }
        policy_get["bindings"].append(binding)

        # set the iam policy to version 3 as that is the schema version that allows for the condition object
        # https://cloud.google.com/iam/docs/policies#versions
        policy_get["version"] = 3

        # make the donuts
        try:
            policy_update = policy = (
                service.projects()
                    .setIamPolicy(resource=project_id, body={"policy": policy_get})
                    .execute()
            )
            print ("Temporary privledges granted until " + str(end_time))
            return (policy_update)

        except HttpError as e:
            error = json.loads(e.content)
            error = error['error']['message']
            return (error)


    def delete_iam_permission(project_id, role, user):
        service = gce_discovery.build('cloudresourcemanager', 'v1', credentials=credentials)

        role = "roles/" + role
        member = "user:" + user

        policy_get = get_iam_policy(project_id)

        for b in policy_get["bindings"]:
            if b["role"] == role:
                binding = b
                break
        for m in binding["members"]:
            if member in m:
                binding["members"].remove(member)

        policy_update = policy = (
            service.projects()
                .setIamPolicy(resource=project_id, body={"policy": policy_get})
                .execute()
        )



    project_id = "testproject-234234234234"
    role = "compute.admin"
    length_in_hours = 1

    # good user
    user = "user@user.com"

    # bad user
    #user = "no_funciona@protonmail.com"

    add_permanent_iam_permissions(project_id, role, user)
    #print (temporary_iam_permissions(project_id, role, user, length_in_hours))
    #print(json.dumps(get_iam_policy(project_id)))
    #delete_iam_permission(project_id, role, user)
    #print(json.dumps(get_iam_policy(project_id)))


if __name__ == "__main__":
    main()


    # ----- NOT RELEVANT TO USER PERMISSIONING ------
    # billing_id = "01106D-7141AE-F072E4"
    #create_project(project_id)
    #add_sub_billing_account(project_id)

    # trash
    # open_console(project_id)