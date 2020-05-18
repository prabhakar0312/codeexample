import json
import sys
import subprocess
import re

admin_accesstoken = '5784df32c7d2e9cc071bfaf3240e9144161f48c04cb349e225e7af1a047b12dc'
filename = sys.argv[1]

product_deploy_config=json.loads(readFile(filename))
admin_url = '3scale-admin.apps.api.abgapiservices.com'

remote_name = 'abg-cicd'

add_remote_cmd = '3scale -k remote add abg-cicd ' + admin_url
add_remote = subprocess.check_output(add_remote_cmd, shell=True, universal_newlines=True)

#Create API Product
apply_product_cmd = '3scale -k service apply ' + remote_name + ' ' + product_deploy_config[product_name] + \
									' -a oidc -n ' + product_deploy_config[product_name]
apply_product = subprocess.check_output(apply_product_cmd, shell=True, universal_newlines=True)
service_id = apply_product.split(":")[1].strip()
print "Product Created =>" + service_id

#Apply API Product - Proxy Configuration
product_proxy_cmd = 'curl -k -s -X PATCH "https://' + admin_url + \
										'/admin/api/services/' + service_id + '/proxy.xml"' + \
										' -d \'access_token=' + admin_accesstoken + '\'' + \
							      ' --data-urlencode \'oidc_issuer_endpoint=' + product_deploy_config[oidc_endpoint] + '\'' + \
							      ' --data-urlencode \'sandbox_endpoint=' + product_deploy_config[sandbox_endpoint] + '\'' + \
							      ' --data-urlencode \'endpoint=' + product_deploy_config[endpoint] + '\''
product_proxy = subprocess.check_output(product_proxy_cmd, shell=True, universal_newlines=True)

#Promote to Staging
promote_staging_cmd= 'curl -k -s  -X POST "https://' + admin_url + \
					'/admin/api/services/' + str(service_id) + \
           '/proxy/deploy.xml?access_token=' + admin_accesstoken + '"';
promote_staging = subprocess.check_output(promote_staging_cmd, shell=True, universal_newlines=True)

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