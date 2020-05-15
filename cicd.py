import json
import sys
import subprocess
import re

def getServiceId(product_copy):
	service_id = re.search(r'new service id (\d+).*$', product_copy, re.DOTALL).group(1)
	return service_id;

def readFile(filename):
	file = open(filename)
	file_text = file.read()
	file.close()
	return file_text

def getBackendId(backends, backend_system_name):
	backend_id = 0
	for backend in backends['backend_apis']:
		system_name = backend["backend_api"]["system_name"]
		if (system_name == backend_system_name):
			backend_id = backend["backend_api"]["id"]
			break
	return backend_id

filename = sys.argv[1]
env_to_promote = sys.argv[2]
source_admin_url = sys.argv[3]
destination_admin_url = sys.argv[4]

admin_url_regex = re.compile(r'https://(\w+)@(.*)$')
admin_accesstoken = admin_url_regex.search(destination_admin_url).group(1)
curl_url = admin_url_regex.search(destination_admin_url).group(2)
print 'Access Token =>' + admin_accesstoken
print 'Curl URL =>' + curl_url
print 'filename' => filename
print 'env_to_promote' => env_to_promote
print 'source_admin_url' => source_admin_url
print 'destination_admin_url' => destination_admin_url

add_remote_cmd = '3scale -k remote add abg-cicd ' + destination_admin_url
add_remote = subprocess.check_output(add_remote_cmd, shell=True, universal_newlines=True)

environment = json.loads(readFile(filename))
print 'environment' => environment

#zyncsso_url = environment[env_to_promote]["zyncsso_url"]
#print "Zync SSO URL->" + zyncsso_url

#Copy and update product
for product in environment[env_to_promote]["products"]:
	#copy product
	product_copy_cmd = '3scale -k product copy -s ' + source_admin_url + \
							' -d ' + destination_admin_url + ' ' + product["product"]
	product_copy = subprocess.check_output(product_copy_cmd, shell=True, universal_newlines=True)
	#print product_copy
	print "Now updating product=>" + product["product"]
	print "Name->" + product["product"]
	print "Staging URL->" + product["staging_public_baseurl"]
	print "Production URL->" + product["production_public_baseurl"]
	zyncsso_url = product["zyncsso_url"]
	print "Zync SSO URL->" + zyncsso_url
	#get service id
	service_id = getServiceId(product_copy)
	#get_products_cmd= 'curl -k -s -X GET "https://' + curl_url + \
	#					'/admin/api/services.xml?access_token=' + admin_accesstoken + '"'
	#print get_products_cmd
	product_proxy_cmd = 'curl -k -s -X PATCH "https://' + curl_url + \
										'/admin/api/services/' + str(service_id) + '/proxy.xml"' + \
										' -d \'access_token=' + admin_accesstoken + '\'' + \
							      ' --data-urlencode \'oidc_issuer_endpoint=' + zyncsso_url + '\'' + \
							      ' --data-urlencode \'sandbox_endpoint=' + \
							      product["staging_public_baseurl"] + '\'' + \
							      ' --data-urlencode \'endpoint=' + \
							      product["production_public_baseurl"] + '\''
	#print product_proxy_cmd
	product_proxy = subprocess.check_output(product_proxy_cmd, shell=True, universal_newlines=True)
	product["id"] = service_id

#Update Backends
get_backends_cmd= 'curl -k -s  -X GET "https://' + curl_url + '/admin/api/backend_apis.json?' + \
                   'access_token=' + admin_accesstoken + '"';
backends = json.loads(subprocess.check_output(get_backends_cmd, shell=True, universal_newlines=True))
for backend in environment[env_to_promote]["backends"]:
		#print backend["backend"]
		backend_id = getBackendId(backends, backend["backend"])
		#print backend_id
		update_backend_cmd = 'curl -k -s -X PUT "https://' + curl_url + \
						'/admin/api/backend_apis/' + str(backend_id) + '.json?access_token=' + \
						admin_accesstoken + '"' + \
						' --data-urlencode \'private_endpoint=' + \
							      backend["private_base_url"] + '\''
		print update_backend_cmd				
		update_backend = subprocess.check_output(update_backend_cmd, shell=True, universal_newlines=True)						


#promote now
for product in environment[env_to_promote]["products"]:
	service_id = product["id"]
	promote_staging_cmd= 'curl -k -s  -X POST "https://' + curl_url + \
						'/admin/api/services/' + str(service_id) + \
    	       '/proxy/deploy.xml?access_token=' + admin_accesstoken + '"';
	promote_staging = subprocess.check_output(promote_staging_cmd, shell=True, universal_newlines=True)

	promte_prod_cmd = '3scale -k proxy-config promote abg-cicd ' + product["product"]
	print promte_prod_cmd
	promte_prod_cmd = subprocess.check_output(promte_prod_cmd, shell=True, universal_newlines=True)

