import cloudfoundry_client
import getpass
import time
import urllib
import zipfile
import os,shutil

un=''
pwd=''
def login_to_cf():
	try:
		global un,pwd
		api_end_point=raw_input("\nAPI Endpoint :")
		username=raw_input("\nEmail>")
		pwd1=getpass.getpass("Password>")
		un=username
		pwd=pwd1
		print 'Connecting to...',api_end_point
		cl=cloudfoundry_client.CloudFoundryClient(api_end_point)
		print '\nAuthenticating...'
		cl.init_with_credentials(username,pwd1)
		print 'Ok'
		return cl
	except Exception , err:
		print err
		return login_to_cf()


def show_all_orgs(cl,url):
	orgs=cl.credentials_manager.get(url)
	all_orgs=[]
	c=1
	for i in orgs['resources']:
		all_orgs.append(i)
	if len(all_orgs)==1:
		print 'Targeted org '+all_orgs[0]['entity']['name']
		return all_orgs[0]
	else:
		print "\nSelect your Organization"
		for i in all_orgs:
			print c,i['entity']['name']
			c+=1
		num=input("\nOrg>")
		num=num-1
	return all_orgs[num]

def show_all_spaces(cl,url):
	all_spaces=[]
	c=1
	spaces=cl.credentials_manager.get(cl.target_endpoint+url)
	for i in spaces['resources']:
		all_spaces.append(i)
	if len(all_spaces)==1:
		print 'Targeted space '+all_spaces[0]['entity']['name']
		return all_spaces[0]
	else:
		print "\nSpaces in your Org"
		for i in all_spaces:
			print c,i['entity']['name']
			c+=1
		try:
			num=input("\nSpace>")
			num=num-1
			return all_spaces[num]
		except Exception,err:
			print '\nInvalid Selection'
			num=input('\nChoose Space Correctly>')
			return all_spaces[num-1]
def app_not_in(all_apps,name):
	c=0
	for i in all_apps:
		if i['entity']['name']==name:
			return c
		c+=1
	return -1


def goto_process1(app):
	print app['entity']['name'],app['metadata']['guid']
	try:
		remove_binding_services(cl,app)
		unmapp_delete_routes(cl,app)
		print '\nStopping the application '+app['entity']['name']+"..."
		cl.application.stop(app['metadata']['guid'])
		print 'Ok\n\nDeleting app '+app['entity']['name']+'...'
		cl.application._remove(app['metadata']['guid'])
		print 'Ok'
	except Exception ,err:
		print err


def manage_apps(cl,url):
	all_apps=[]
	c=1
	flag=0
	print "\nAll apps in you space"
	apps=cl.credentials_manager.get(cl.target_endpoint+url)
	for i in apps['resources']:
		all_apps.append(i)
	print '\nTotal no.of apps '+str(len(all_apps))
	for i in all_apps:
		print c,i['entity']['name'],i['entity']['state']
		if c%10==0:
			num=raw_input("\nChoose app (or) next(Enter) (or) App name>")
			try:
				num=int(num)
				num=num-1
				flag=1
				app=all_apps[num]
				n=raw_input('\nYou selected '+app['entity']['name']+' y/n>')
				if n.lower()=='y':
					goto_process1(app)
					app_data={'name':app['entity']['name'],"space_guid":space['metadata']['guid'],"diego":True}
					return app_data
			except Exception ,err:
				print err
				ind=app_not_in(all_apps,num)
				if num!='' and ind==-1:
					print 'App '+num+' not existed...'
					conf=raw_input('\nCreate app with name '+num+ '  y/n >')
					if conf.lower()=='y':
						app_data={'name':num,"space_guid":space['metadata']['guid'],"diego":True}
						flag=1
						return app_data
				elif ind!=-1:
					print '\n Selecting app '+num
					app=all_apps[ind]
					goto_process1(app)
					app_data={'name':app['entity']['name'],"space_guid":space['metadata']['guid'],"diego":True}
					return app_data

				c=c
		c+=1
	if flag==0:
		name=raw_input("Choose app (or) New app name>")
		try:
			name=int(name)
			app=all_apps[name-1]
			goto_process1(app)
			app_data={'name':app['entity']['name'],"space_guid":space['metadata']['guid'],"diego":True}
			return app_data
		except:
			if name=='':
				print '\nInvalid Selection'
				return manage_apps(cl,url)
			else:
				app_data={'name':name,"space_guid":space['metadata']['guid'],"diego":True}
				return app_data




	

def remove_binding_services(cl,app):
	all_bindings=cl.credentials_manager.get(cl.target_endpoint+app['entity']['service_bindings_url'])
	app_guid=app['metadata']['guid']
	for i in all_bindings['resources']:
		print "\nUnbinding ... Sevices"
		cl.credentials_manager.delete(cl.application.base_url+"/"+app_guid+"/service_bindings/"+i['metadata']['guid'])
		print 'Ok'

def unmapp_delete_routes(cl,app):
	app_guid=app['metadata']['guid']
	print '\nUnmapping routes ....'
	all_routes=cl.credentials_manager.get(cl.target_endpoint+app['entity']['routes_url'])
	for i in all_routes['resources']:
		cl.credentials_manager.delete(cl.application.base_url+"/"+app_guid+"/routes/"+i['metadata']['guid'])
		print 'Ok'
		print '\nDeleting orphan route...'
		cl.credentials_manager.delete(cl.target_endpoint+"/v2/routes/"+i['metadata']['guid'])
		print 'Ok'

def create_route(cl,app):
	domains=cl.credentials_manager.get(cl.target_endpoint+"/v2/domains")
	all_domains=[]
	c=1
	for i in domains['resources']:
		all_domains.append(i)
	if len(all_domains)==1:
		domain=all_domains[0]
	else:
		print '\nSelect a domain'
		for i in all_domains:
			print c,i['entity']['name']
			c+=1
		try:
			num=input("Choose domain>")
		except:
			print '\nInvalid Selection'
			num=input('\nChoose domain>')
		num=num-1
		domain=all_domains[num]
	space_guid=app['entity']['space_guid']
	route_data={"domain_guid":domain['metadata']['guid'],"space_guid":space_guid,"host":app['entity']['name']}
	print '\nCreating a route in domain '+domain['entity']['name']+' for '+app['entity']['name']+'...'
	route=cl.credentials_manager.post(cl.target_endpoint+"/v2/routes",route_data)
	print 'Ok\n\nMapping to app ...'
	cl.credentials_manager.put(cl.target_endpoint+"/v2/routes/"+route['metadata']['guid']+"/apps/"+app['metadata']['guid'],'')
	print 'Ok\n'


def get_required_instance(cl,plan,app):
	print '\nGetting Service Instances for '+plan['entity']['name']
	instances=cl.credentials_manager.get(cl.target_endpoint+plan['entity']['service_instances_url'])
	service_instances=[]
	c=1
	for i in instances['resources']:
		print c,i['entity']['name']
		service_instances.append(i)
		c+=1
	if c==1:
		print '\nCreating New Service Instance'
		inst_name=raw_input("Service Instance Name>")
		instance_data={"space_guid":app['entity']['space_guid'],"name":inst_name,"service_plan_guid":plan['metadata']['guid']}
		instance=cl.credentials_manager.post(cl.service_instance.base_url,instance_data)
		return instance
	else:
		num=raw_input("\nSelect Instance or Enter New Instance name>")
		try:
			num=int(num)
			num=num-1
			return service_instances[num]
		except Exception,err:
			if err.message=='list index out of range':
				print '\nInalid Selection'
				return get_required_instance(cl,plan,app)
			serv_inst_data={"space_guid":app['entity']['space_guid'],"name":num,"service_plan_guid":plan['metadata']['guid']}
			instance=cl.credentials_manager.post(cl.service_instance.base_url,serv_inst_data)
			return instance




def manage_services(cl,app,org):
	print '\nListing all services...'
	#services=cl.credentials_manager.get(cl.target_endpoint+"/v2/services")
	services=cl.credentials_manager.get(cl.organization.base_url+"/"+org['metadata']['guid']+"/services")
	all_services=[]
	c=1
	flag=0
	for i in services['resources']:
		all_services.append(i)
		print c,i['entity']['label']
		if c%10==0:
			num=raw_input("\nChoose Service or next(Enter)>")
			try:
				num=int(num)
				flag=1
				break
			except:
				c=c
		c+=1
	if flag==0:
		try:
			num=input("\nChoose Service>")
		except:
			print '\nInvalid Choice'
			num=input('\nChoose Service>')
	num=num-1
	service=all_services[num]

	print '\nListing service plans ...'
	plans=cl.credentials_manager.get(cl.target_endpoint+service['entity']['service_plans_url'])
	all_plans=[]
	c=1
	for i in plans['resources']:
		all_plans.append(i)
		print c,i['entity']['name']
		c+=1
	num=input("\nPlan>")
	num=num-1
	plan=all_plans[num]

	service_instance=get_required_instance(cl,plan,app)
	print '\nBinding Service to app...'
	binding_data={"app_guid":app['metadata']['guid'],"service_instance_guid":service_instance['metadata']['guid']}
	cl.credentials_manager.post(cl.service_binding.base_url,binding_data)
	print '\nOk'




try:
	cl=login_to_cf()
	org=show_all_orgs(cl,cl.organization.base_url)
	space=show_all_spaces(cl,org['entity']['spaces_url'])


	app_data=manage_apps(cl,space['entity']['apps_url'])
	print '\nCreating new app with name '+app_data['name']
	app=cl.application._create(app_data)
	print 'Ok\n'

	create_route(cl,app)

	manage_services(cl,app,org)

	app_files_url=raw_input("Zip File url>")
#open_zip=urllib.urlopen("https://github.com/pivotal-cf/cf-redis-example-app/archive/master.zip")
	open_zip=urllib.urlopen(app_files_url)
	print '\nDownloading zip file...'
	file_zip=open("application.zip","wb")
	file_zip.write(open_zip.read())
	file_zip.close()
	print 'Ok\n'

	file1=zipfile.ZipFile("application.zip")
	file1.extractall("application")
	file1.close()

	os.chdir("application")
	dir_1=os.listdir(os.getcwd())[0]
	os.chdir(dir_1)
	os.popen("cf api "+cl.target_endpoint).read()
	os.popen("cf login -u "+un+" -p "+pwd+" -o "+org['entity']['name']+" -s "+space['entity']['name']).read()
	os.system("cf push "+app['entity']['name'])#+" --no-start")
	os.chdir('..')
	os.chdir('..')
	shutil.rmtree('application')
	os.remove('application.zip')

except Exception,err:
	print err

#org=get_required_org(raw_input("Org>"),cl)
'''

	up=app['metadata']['updated_at']

	try:
		cl.application.start(app['metadata']['guid'])
	except Exception,err:
		time.sleep(10)
		print '\nStill Staging'
		try:
			cl.application.start(app['metadata']['guid'])
		except:
			print '\nStaging about to complete'
	time.sleep(5)
	if app['entity']['state']=='STARTED':
		print 'Staging Completed...'
	while( app['entity']['state']=='STOPPED'):
		time.sleep(5)
		app=cl.application.get(app['metadata']['guid'])

	print '\n\n'+app['entity']['name'],'',app['entity']['state']

'''



#print space['entity']['name'],space['metadata']['guid']
