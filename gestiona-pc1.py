import os
from subprocess import call
import json
import sys
import logging
from lxml import etree


def create():
	if (len(sys.argv) == 3):
		num_serv = int(sys.argv[2])
	else:
		num_serv = 2

	if ((num_serv < 1) or (num_serv > 5)):
		raise Exception("formato incorrecto")


	call(["cat", ">>", "gestiona-pc1.json"]) 
	json.dump({"num_serv": num_serv, "debug": "false"}, open("gestiona-pc1.json", "w"), indent = 4)

	jsond = open("gestiona-pc1.json", "r")
	jsonDecoded = json.loads(jsond.read())
	debugboolean = jsonDecoded["debug"]
	jsond.close()

	if debugboolean == 'true':
		logging.basicConfig(level=logging.DEBUG)
	elif debugboolean == 'false':
		logging.basicConfig(level=logging.INFO)
	else :
		raise Exception("error fichero JSON")
	logger = logging.getLogger('gestiona-pc1')


	for i in range(1, num_serv + 1):
		
		itext = str(i)

		call(["qemu-img", "create", "-f", "qcow2", "-b", "cdps-vm-base-pc1.qcow2", "s"+itext+".qcow2"])
		call(["cp", "plantilla-vm-pc1.xml", "s"+itext+".xml"])
		logger.debug("ficheros de s"+itext+" copiados correctamente")

		#sX
		tree = etree.parse("s"+itext+".xml")
		root = tree.getroot()

		name = root.find("name")
		name.text = "s"+itext

		source = root.find("./devices/disk/source")
		source.set("file", "/mnt/tmp/a.villasecam/s"+itext+".qcow2")

		source = root.find("./devices/interface/source")
		source.set("bridge", "LAN2")

		open("s"+itext+".xml", "w").write(etree.tounicode(tree, pretty_print = True))
		logger.debug("fichero xml de s"+itext+" modificado correctamente")
		logger.info("maquina virtual de s"+itext+" creada correctamente")


	#lb
	call(["qemu-img", "create", "-f", "qcow2", "-b", "cdps-vm-base-pc1.qcow2", "lb.qcow2"])
	call(["cp", "plantilla-vm-pc1.xml", "lb.xml"])
	logger.debug("ficheros de lb copiados correctamente")

	
	tree = etree.parse('lb.xml')
	root = tree.getroot()

	name = root.find("name")
	name.text = "lb"

	source = root.find("./devices/disk/source")
	source.set("file", "/mnt/tmp/a.villasecam/lb.qcow2")

	source = root.find("./devices/interface/source")
	source.set("bridge", "LAN2")

	i1 = etree.Element("interface", type='bridge')
	source = etree.SubElement(i1, "source", bridge='LAN1')
	source = etree.SubElement(i1, "model", type='virtio')

	device = root.find("./devices")
	device.insert(2, i1)

	open("lb.xml", "w").write(etree.tounicode(tree, pretty_print = True))
	
	logger.debug("fichero xml de lb modificado correctamente")
	logger.info("maquina virtual de lb creada correctamente")

	#C1

	call(["qemu-img", "create", "-f", "qcow2", "-b", "cdps-vm-base-pc1.qcow2", "c1.qcow2"])
	call(["cp", "plantilla-vm-pc1.xml", "c1.xml"])
	logger.debug("ficheros de c1 copiados correctamente")

	tree = etree.parse('c1.xml')
	root = tree.getroot()

	name = root.find("name")
	name.text = "c1"

	source = root.find("./devices/disk/source")
	source.set("file", "/mnt/tmp/a.villasecam/c1.qcow2")

	source = root.find("./devices/interface/source")
	source.set("bridge", "LAN1")

	open("c1.xml", "w").write(etree.tounicode(tree, pretty_print = True))

	logger.debug("fichero xml de c1 modificado correctamente")
	logger.info("maquina virtual de c1 creada correctamente")

	call(["sudo", "brctl", "addbr", "LAN1"])
	logger.debug("bridge LAN1 añadido correctamente ")
	call(["sudo", "ifconfig", "LAN1", "up"])
	logger.debug("bridge LAN1  up")
	logger.info("bridge LAN1 creado e iniciado")
	call(["sudo", "brctl", "addbr", "LAN2"])
	logger.debug("bridge LAN2 añadido correctamente ")
	call(["sudo", "ifconfig", "LAN2", "up"])
	logger.debug("bridge LAN2  up")
	logger.info("bridge LAN2 creado e iniciado")

	call(["HOME=/mnt/tmp", "sudo", "virt-manager"], shell = True)
	logger.debug("directorio de virt-manager establecido en /mnt/tmp")
	logger.info("directorio de virt-manager cambiado")

	for i in range(1, num_serv + 1):
		
		itext = str(i)

		call(["sudo", "virsh", "define", "s"+itext+".xml"])
		logger.debug("maquina s"+itext+" ha sido definida")


	call(["sudo", "virsh", "define", "lb.xml"])
	logger.debug("maquina lb ha sido definida")
	call(["sudo", "virsh", "define", "c1.xml"])
	logger.debug("maquina c1 ha sido definida")
	logger.info("maquinas del proyecto han sido definidas")	

	for i in range(1, num_serv + 1):
		
		itext = str(i)

		#hostname
		os.system('echo s'+itext+'> hostname')
		call(["sudo", "virt-copy-in", "-a", 's'+itext+'.qcow2', "hostname", "/etc"])
		logger.debug("hostname de s"+itext+" modificado correctamente")

		# hosts
		os.system('echo "127.0.1.1 s'+itext+'"> hosts')
		os.system('echo "127.0.0.1 localhost" >> hosts')
		os.system('echo "::1 localhost ip6-localhost ips-loopback" >> hosts')
		os.system('echo "ff02::1 ip6-allnodes" >> hosts')
		os.system('echo "ff02::2 ip6-allrouters" >> hosts')
		call(["sudo", "virt-copy-in", "-a", 's'+itext+'.qcow2', "hosts", "/etc"])
		logger.debug("fichero hosts de s"+itext+" modificado correctamente")


		#interfaces
		os.system('echo "auto lo"> interfaces')
		os.system('echo "iface lo inet loopback" >> interfaces')
		os.system('echo "auto eth0" >> interfaces')
		os.system('echo "iface eth0 inet static" >> interfaces')
		os.system('echo "address 10.20.2.10'+itext+'" >> interfaces')
		os.system('echo "netmask 255.255.255.0" >> interfaces')
		os.system('echo "gateway 10.20.2.1" >> interfaces')	
		call(["sudo", "virt-copy-in", "-a", 's'+itext+'.qcow2', "interfaces", "/etc/network"])
		logger.debug("fichero de interfaces de s"+itext+" modificado correctamente")


	#lb

	#hostname
	os.system('echo lb> hostname')
	call(["sudo", "virt-copy-in", "-a", 'lb.qcow2', "hostname", "/etc"])
	logger.debug("hostname de lb modificado correctamente")

	#hosts
	os.system('echo "127.0.1.1 lb"> hosts')
	os.system('echo "127.0.0.1 localhost" >> hosts')
	os.system('echo "::1 localhost ip6-localhost ips-loopback" >> hosts')
	os.system('echo "ff02::1 ip6-allnodes" >> hosts')
	os.system('echo "ff02::2 ip6-allrouters" >> hosts')
	call(["sudo", "virt-copy-in", "-a", 'lb.qcow2', "hosts", "/etc"])
	logger.debug("fichero hosts de lb modificado correctamente")

	#interfaces
	os.system('echo "auto lo"> interfaces')
	os.system('echo "iface lo inet loopback" >> interfaces')
	#eth0
	os.system('echo "auto eth0" >> interfaces')
	os.system('echo "iface eth0 inet static" >> interfaces')
	os.system('echo "address 10.20.1.1" >> interfaces')
	os.system('echo "netmask 255.255.255.0" >> interfaces')
	#eth1
	os.system('echo "auto eth1" >> interfaces')
	os.system('echo "iface eth1 inet static" >> interfaces')
	os.system('echo "address 10.20.2.1" >> interfaces')
	os.system('echo "netmask 255.255.255.0" >> interfaces')
	call(["sudo", "virt-copy-in", "-a", 'lb.qcow2', "interfaces", "/etc/network"])
	logger.debug("fichero de interfaces de lb modificado correctamente")


	#c1
	#hostname
	os.system('echo c1> hostname')
	call(["sudo", "virt-copy-in", "-a", 'c1.qcow2', "hostname", "/etc"])
	logger.debug("hostname de c1 modificado correctamente")

	# hosts
	os.system('echo "127.0.1.1 c1"> hosts')
	os.system('echo "127.0.0.1 localhost" >> hosts')
	os.system('echo "::1 localhost ip6-localhost ips-loopback" >> hosts')
	os.system('echo "ff02::1 ip6-allnodes" >> hosts')
	os.system('echo "ff02::2 ip6-allrouters" >> hosts')
	call(["sudo", "virt-copy-in", "-a", 'c1.qcow2', "hosts", "/etc"])
	logger.debug("fichero hosts de c1 modificado correctamente")

	#interfaces
	os.system('echo "auto lo"> interfaces')
	os.system('echo "iface lo inet loopback" >> interfaces')
	os.system('echo "auto eth0" >> interfaces')
	os.system('echo "iface eth0 inet static" >> interfaces')
	os.system('echo "address 10.20.1.2" >> interfaces')
	os.system('echo "netmask 255.255.255.0" >> interfaces')
	os.system('echo "gateway 10.20.1.1" >> interfaces')	
	call(["sudo", "virt-copy-in", "-a", 'c1.qcow2', "interfaces", "/etc/network"])
	logger.debug("fichero de interfaces de c1 modificado correctamente")
	logger.info("ficheros de red modificados de todas las máquinas virtuales")

	#HOST
	call(["sudo", "ifconfig", "LAN1", "10.20.1.3/24"])
	call(["sudo", "ip", "route", "add", "10.20.0.0/16", "via", "10.20.1.1"])

	#paginas web
	for i in range(1, num_serv + 1):
		itext = str(i)
		os.system('echo "S'+itext+'"> index.html')
		call(["sudo", "virt-copy-in", "-a", 's'+itext+'.qcow2', "index.html", "/var/www/html"])
		logger.debug("fichero html de s"+itext+" modificado correctamente")


	#configuracion de haproxy

	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg:'")
	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg: frontend lb'")
	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg: 	bind *:80'")
	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg: 	mode http'")
	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg: 	default_backend webservers'")
	logger.debug("frontend lb modificado")
	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg:'")
	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg:'")
	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg: backend webservers'")
	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg: 	mode http'")
	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg: 	balance roundrobin'")
	
	for i in range(1, num_serv + 1):
		itext = "'/etc/haproxy/haproxy.cfg: 	server s" + str(i)+" 10.20.2.10"+str(i)+":80 check'"
		os.system("sudo virt-customize -a lb.qcow2 --append-line " + itext)
	logger.debug("backend webservers modificado")
	
	os.system("sudo virt-edit -a lb.qcow2 /etc/sysctl.conf -e 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/'")
	logger.debug("balanceador de trafico configurado como router")

	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg:'")
	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg: global'")
	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg: 	stats socket ipv4@127.0.0.1:9999 level admin'")
	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg: 	stats socket /var/run/hapee-lb.sock mode 666 level admin'")
	os.system("sudo virt-customize -a lb.qcow2 --append-line '/etc/haproxy/haproxy.cfg: 	stats timeout 2m'")
	logger.debug("consola ha proxy habilitada")

	logger.info("balanceador configurado")


def start():

	jsond = open("gestiona-pc1.json", "r")
	jsonDecoded = json.loads(jsond.read())
	debugboolean = jsonDecoded["debug"]
	num_serv_abrir = int(jsonDecoded["num_serv"])
	jsond.close()

	if debugboolean == 'true':
		logging.basicConfig(level=logging.DEBUG)
	elif debugboolean == 'false':
		logging.basicConfig(level=logging.INFO)
	else :
		raise Exception("error fichero JSON")
	logger = logging.getLogger('gestiona-pc1')

	if (len(sys.argv) == 3):
		serv = sys.argv[2]
		if serv == "s1":
			call(["sudo", "virsh", "start", "s1"])
			logger.debug("s1 iniciada")
			os.system('xterm -e "sudo virsh console s1" &')
			logger.debug("mostrar terminal de s1")
			logger.info("s1 iniciado correctamente")
		elif serv == "s2":
			call(["sudo", "virsh", "start", "s2"])
			logger.debug("s2 iniciada")
			os.system('xterm -e "sudo virsh console s2" &')
			logger.debug("mostrar terminal de s2")
			logger.info("s2 iniciado correctamente")
		elif serv == "s3":
			if num_serv_abrir > 2:
				call(["sudo", "virsh", "start", "s3"])
				logger.debug("s3 iniciada")
				os.system('xterm -e "sudo virsh console s3" &')
				logger.debug("mostrar terminal de s3")
				logger.info("s3 iniciado correctamente")
			else:
				raise Exception("No existe este servidor")
		elif serv == "s4":
			if num_serv_abrir > 3:
				call(["sudo", "virsh", "start", "s4"])
				logger.debug("s4 iniciada")
				os.system('xterm -e "sudo virsh console s4" &')
				logger.debug("mostrar terminal de s4")
				logger.info("s4 iniciado correctamente")
			else:
				raise Exception("No existe este servidor")
		elif serv == "s5":
			if num_serv_abrir == 5:
				call(["sudo", "virsh", "start", "s5"])
				logger.debug("s5 iniciada")
				os.system('xterm -e "sudo virsh console s5" &')
				logger.debug("mostrar terminal de s5")
				logger.info("s5 iniciado correctamente")
			else:
				raise Exception("No existe este servidor")
		elif serv == "lb":
			call(["sudo", "virsh", "start", "lb"])
			logger.debug("lb iniciada")
			os.system('xterm -e "sudo virsh console lb" &')
			logger.debug("mostrar terminal de lb")
			logger.info("lb iniciado correctamente")
		elif serv == "c1":
			call(["sudo", "virsh", "start", "c1"])
			logger.debug("c1 iniciada")
			os.system('xterm -e "sudo virsh console c1" &')
			logger.debug("mostrar terminal de c1")
			logger.info("c1 iniciado correctamente")
		else:
			raise Exception("Comando erroneo")
		quit()


	for i in range(1, num_serv_abrir + 1):
		
		itext = str(i)
		call(["sudo", "virsh", "start", "s"+itext])
		logger.debug("s"+itext+" iniciada")
		os.system('xterm -e "sudo virsh console s'+itext+'" &')
		logger.debug("mostrar terminal de s"+itext)

	logger.info("servidores iniciados correctamente")

	call(["sudo", "virsh", "start", "lb"])
	logger.debug("lb iniciada")
	os.system('xterm -e "sudo virsh console lb" &')
	logger.debug("mostrar terminal de lb")
	logger.info("lb iniciado correctamente")

	call(["sudo", "virsh", "start", "c1"])
	logger.debug("c1 iniciada")
	os.system('xterm -e "sudo virsh console c1" &')
	logger.debug("mostrar terminal de c1")
	logger.info("c1 iniciado correctamente")

def stop():

	jsond = open("gestiona-pc1.json", "r")
	jsonDecoded = json.loads(jsond.read())
	debugboolean = jsonDecoded["debug"]
	num_serv_parar = int(jsonDecoded["num_serv"])
	jsond.close()

	if debugboolean == 'true':
		logging.basicConfig(level=logging.DEBUG)
	elif debugboolean == 'false':
		logging.basicConfig(level=logging.INFO)
	else :
		raise Exception("error fichero JSON")
	logger = logging.getLogger('gestiona-pc1')

	if (len(sys.argv) == 3):
		serv = sys.argv[2]
		if serv == "s1":
			call(["sudo", "virsh", "shutdown", "s1"])
			logger.info("s1 apagado")
		elif serv == "s2":
			call(["sudo", "virsh", "shutdown", "s2"])
			logger.info("s2 apagado")
		elif serv == "s3":
			if num_serv_parar > 2:
				call(["sudo", "virsh", "shutdown", "s3"])
				logger.info("s3 apagado")
			else:
				raise Exception("No existe este servidor")
		elif serv == "s4":
			if num_serv_parar > 3:
				call(["sudo", "virsh", "shutdown", "s4"])
				logger.info("s4 apagado")
			else:
				raise Exception("No existe este servidor")
		elif serv == "s5":
			if num_serv_parar == 5:
				call(["sudo", "virsh", "shutdown", "s5"])
				logger.info("s5 apagado")
			else:
				raise Exception("No existe este servidor")
		elif serv == "lb":
			call(["sudo", "virsh", "shutdown", "lb"])
			logger.info("lb apagado")
		elif serv == "c1":
			call(["sudo", "virsh", "shutdown", "c1"])
			logger.info("c1 apagado")
		else:
			raise Exception("Comando erroneo")
		quit()

	for i in range(1, num_serv_parar + 1):
		
		itext = str(i)
		call(["sudo", "virsh", "shutdown", "s"+itext])
		logger.debug("s"+itext+" apagado")
	logger.info("servers apagados")
	call(["sudo", "virsh", "shutdown", "lb"])
	logger.info("lb apagado")
	call(["sudo", "virsh", "shutdown", "c1"])
	logger.info("c1 apagado")

def destroy():

	jsond = open("gestiona-pc1.json", "r")
	jsonDecoded = json.loads(jsond.read())
	debugboolean = jsonDecoded["debug"]
	num_serv_borrar = int(jsonDecoded["num_serv"])
	jsond.close()

	if debugboolean == 'true':
		logging.basicConfig(level=logging.DEBUG)
	elif debugboolean == 'false':
		logging.basicConfig(level=logging.INFO)
	else :
		raise Exception("error fichero JSON")
	logger = logging.getLogger('gestiona-pc1')

	for x in range(1, num_serv_borrar + 1):
		call(["sudo", "virsh", "destroy", "s"+str(x)])
		call(["sudo", "virsh", "undefine", "s"+str(x)])
		logger.debug("s"+str(x)+" destruido")
		call(["rm", "-rf", "s"+str(x)+".xml"])
		call(["rm", "-rf", "s"+str(x)+".qcow2"])
		logger.debug("archivos de s"+str(x)+" eliminados")
		
	logger.info("Servidores eliminados")
	
	call(["sudo", "virsh", "destroy", "lb"])
	call(["sudo", "virsh", "undefine", "lb"])
	logger.debug("lb destruido")
	call(["rm", "lb.xml"])
	call(["rm", "lb.qcow2"])
	logger.debug("ficheros de lb eliminados")
	logger.info("lb eliminado")
	call(["sudo", "virsh", "destroy", "c1"])
	call(["sudo", "virsh", "undefine", "c1"])
	logger.debug("c1 destruido")
	call(["rm", "c1.xml"])
	call(["rm", "c1.qcow2"])
	logger.debug("ficheros de c1 eliminados")
	logger.info("c1 eliminado")

	call(["rm", "hosts"])
	logger.debug("ficheros configuracion hosts eliminado")
	call(["rm", "hostname"])
	logger.debug("ficheros configuracion hostname eliminado")
	call(["rm", "interfaces"])
	logger.debug("ficheros configuracion interfaces eliminado")
	call(["rm", "gestiona-pc1.json"])
	logger.debug("fichero json eliminado")
	logger.info("ficheros de configuracion eliminados")


	call(["sudo", "ifconfig", "LAN1", "down"])
	call(["sudo", "brctl", "delbr", "LAN1"])
	logger.debug("LAN1 eliminada")
	call(["sudo", "ifconfig", "LAN2", "down"])
	call(["sudo", "brctl", "delbr", "LAN2"])
	logger.debug("LAN2 eliminada")
	logger.info("redes LAN eliminadas")

	call(["rm", "index.html"])
def watch():
	os.system("xterm -title monitor -e watch sudo virsh list --all &")


if sys.argv[1] == "create":
	create()
elif sys.argv[1] == "start":
	start()
elif sys.argv[1] == "stop":
	stop()
elif sys.argv[1] == "destroy":
	destroy()
elif sys.argv[1] == "watch":
	watch()
else: 
	raise Exception("Formato incorrecto")
