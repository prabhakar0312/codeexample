  
import json
import sys
import subprocess
import re

def readFile(filename):
	file = open(filename)
	file_text = file.read()
	file.close()
	return file_text

admin_accesstoken = '416989be027cf0866733113a199414993291dd5fa7e04e3dd6eca85fdcfe4e23'
filename = sys.argv[1]
policy_filename = sys.argv[2]
active_docs_filename = sys.argv[3]

active_docs_configs=json.loads(readFile(active_docs_filename))

product_deploy_config=json.loads(readFile(filename))
policy_config=json.loads(readFile(policy_filename))
admin_url = '3scale-admin.dev.apps.api-np.abgapiservices.com'

remote_name = 'abg-cicd'

add_remote_cmd = '3scale -k remote add abg-cicd https://' + admin_accesstoken + '@' +product_deploy_config["admin_url"]
add_remote = subprocess.check_output(add_remote_cmd, shell=True, universal_newlines=True)

#Create API Product
apply_product_cmd = '3scale -k service apply ' + remote_name + ' ' + product_deploy_config["product_system_name"] + \
									' -a oidc -n ' + '"' +product_deploy_config["product_name"] + '"'
apply_product = subprocess.check_output(apply_product_cmd, shell=True, universal_newlines=True)
service_id = apply_product.split(":")[1].strip()
print "Product Created =>" + service_id

#Apply Product Policies
#curl -k -X PUT "https://$PORTAL_ENDPOINT/admin/api/services/$SERVICE_ID/proxy/policies.json" --data "access_token=$TOKEN" --data-urlencode #policies_config@policies_config.json

product_policy_cmd = 'curl -k -s -X PUT -H "Content-Type: application/json" "https://' + admin_url + \
									'/admin/api/services/' + service_id + '/proxy/policies.json?access_token=' + admin_accesstoken +'"' + \
									' -d @' + policy_filename +''
product_policy= subprocess.check_output(product_policy_cmd, shell=True, universal_newlines=True)                                 
print "Product Gateway Policy Command =>" + product_policy_cmd
print "Product Gateway Policy Applied =>" + product_policy


#Apply API Product - Proxy Configuration
product_proxy_cmd = 'curl -k -s -X PATCH "https://' + admin_url + \
										'/admin/api/services/' + service_id + '/proxy.xml"' + \
										' -d \'access_token=' + admin_accesstoken + '\'' + \
							      ' --data-urlencode \'oidc_issuer_endpoint=' + product_deploy_config["oidc_endpoint"] + '\'' + \
							      ' --data-urlencode \'sandbox_endpoint=' + product_deploy_config["sandbox_endpoint"] + '\'' + \
							      ' --data-urlencode \'endpoint=' + product_deploy_config["endpoint"] + '\'' + \
                                  ' --data-urlencode \'api_backend=' + product_deploy_config["api_backend"] + '\'' + \
                                  ' -d \'api_test_path=' + product_deploy_config["api_test_path"] + '\'' + \
                                  ' -d \'oidc_issuer_type=' + "keycloak" + '\''
                                  
product_proxy = subprocess.check_output(product_proxy_cmd, shell=True, universal_newlines=True)
print "Product Proxy Configuration Updated  =>" + service_id

#Apply Product Active Docs
#Apply Product Active Docs
#activedocs_config_spec=json.dumps(activedocs_config["body"]) 

for activedocs_config in active_docs_configs["active_docs_configs"]:
    
    activedocs_config_spec=json.dumps(activedocs_config["body"])
    product_activedocs_cmd = 'curl -k -s -X PUT "https://' + admin_url + \
                                       '/admin/api/active_docs.json"' + \
                                        ' -d \'access_token=' + admin_accesstoken + '\'' + \

                                        ' --data-urlencode \'name=' + activedocs_config["name"] + '\'' + \
                                        ' --data-urlencode \'service_id=' + service_id + '\'' + \
                                        ' --data-urlencode \'body=' + activedocs_config_spec + '\'' + \
                                        ' --data-urlencode \'description=' + activedocs_config["description"] + '\'' + \
                                        ' --data-urlencode \'system_name=' + activedocs_config["system_name"] + '\'' + \
                                        ' --data-urlencode \'skip_swagger_validations=' + activedocs_config["skip_swagger_validations"] + '\''
    print "product_activedocs_cmd " + product_activedocs_cmd
    product_activedocs = subprocess.check_output(product_activedocs_cmd, shell=True, universal_newlines=True)                                 
    print "product_activedocs_cmd " + product_activedocs_cmd
    print "Product Active docs added " + product_activedocs


#Promote to Staging
promote_staging_cmd= 'curl -k -s  -X POST "https://' + admin_url + \
					'/admin/api/services/' + str(service_id) + \
           '/proxy/deploy.xml?access_token=' + admin_accesstoken + '"';
promote_staging = subprocess.check_output(promote_staging_cmd, shell=True, universal_newlines=True)
print "Product Promoted to Staging =>" + promote_staging

#Get Version
get_version_cmd = 'curl -k -s  -X GET "https://' + admin_url + \
					'/admin/api/services/' + str(service_id) + \
           '/proxy/configs/sandbox/latest.json?access_token=' + admin_accesstoken + '"';
get_version = json.loads(subprocess.check_output(get_version_cmd, shell=True, universal_newlines=True))
version = get_version["proxy_config"]["version"]

#Promote to Production
promote_production_cmd= 'curl -k -s  -X POST "https://' + admin_url + \
					'/admin/api/services/' + str(service_id) + \
           '/proxy/configs/sandbox/' + str(version) + '/promote.json?access_token=' \
           + admin_accesstoken + '&to=production"';
promote_production = subprocess.check_output(promote_production_cmd, shell=True, universal_newlines=True)

print "Product Promoted to Production =>"
