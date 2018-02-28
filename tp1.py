import socket
import struct
import sys
import binascii
from optparse import OptionParser

MAX_LENGTH = 65535

def verificacao(cabecalho_recebido, dados_recebidos):
	pacote = (cabecalho_recebido[0], cabecalho_recebido[1], 0, cabecalho_recebido[3], cabecalho_recebido[4], cabecalho_recebido[5], dados_recebidos[0])
	s = struct.Struct('!8s 8s I I I I' + str(cabecalho_recebido[3]) + 's')
	packed_package = s.pack(*pacote)
	chksum = checksum(packed_package)
	return (chksum == cabecalho_recebido[2])


def process_opt():
    usage = "usage: %prog files\n"
    parser = OptionParser(usage=usage)
    parser.add_option("-c", "--cliente", dest="CLIENTE", help="cliente params", nargs=3)
    parser.add_option("-s", "--servidor", dest="SERVIDOR", help="servidor params", nargs=3)  
    opt, files = parser.parse_args()
 
    if (not opt.CLIENTE and not opt.SERVIDOR):
        parser.print_help()
        sys.exit(1)
    if (opt.CLIENTE and opt.SERVIDOR):
        parser.print_help()
        sys.exit(1)        
    return opt

def carry_around_add(a, b):
    c = a + b
    return(c &0xffff)+(c >>16)

def checksum(msg):
    s =0
    for i in range(0, len(msg),2):
        w = ord(msg[i])+(ord(msg[i+1])<<8)
        s = carry_around_add(s, w)
    return~s &0xffff


if __name__ == '__main__':
	opt = process_opt()

s_ack = struct.Struct('!8s 8s I I I I')

if(opt.CLIENTE):
	host, port = opt.CLIENTE[0].split(':')
	inputFile = opt.CLIENTE[1]
	outputFile = opt.CLIENTE[2]
	sync = 'dcc023c2'
	chksum = 0
	length = 0
	idPacote = 0
	flags = 63
	info = []

	tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	dest = (host, int(port))
	print >>sys.stderr, 'connecting to %s port %s' % dest
	tcp.connect(dest)

	try:

		with open(inputFile, 'rb') as f:
			while True:
				aux = f.read(65535)
				if not aux:
					break
				info.append(aux)

		for i, data in enumerate(info):
			length = len(data)
			if (i == len(info) - 1):
				flags = 64
			pacote = (sync, sync, chksum, length, idPacote, flags, data)
			s = struct.Struct('!8s 8s I I I I' + str(length) + 's')
			packed_package = s.pack(*pacote)

			if len(packed_package) % 2 <> 0:
				packed_package += '0'

			chksum = checksum(packed_package)

			pacote = (sync, sync, chksum, length, idPacote, flags, data)
			packed_package = s.pack(*pacote)
			tcp.send(packed_package)
			while True:
				pack_confirmation = tcp.recv(1024)
				unpack_confirmation = s_ack.unpack(pack_confirmation)
				if (unpack_confirmation[5] == 128):
					if (idPacote == 0):
						idPacote = 1
					else: 
						idPacote = 0 
					break
				tcp.send(packed_package)
				time.sleep(1)

	except Exception, e:
			
			print >> sys.stderr, "Exception: %s" % str(e)

	finally:
    
			print 'Finalizando conexao com o servidor', dest
		  	tcp.close()


elif(opt.SERVIDOR):
	host = ''
	port = opt.SERVIDOR[0]
	inputFile = opt.SERVIDOR[1]
	outputFile = opt.SERVIDOR[2]
	sync = 'dcc023c2'
	chksumAnterior = 0
	length = 0
	idPacoteAnterior = 1
	flags = 63

	tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	orig = (host, int(port))

	tcp.bind(orig)
	tcp.listen(1)

	while True:
  		con, cliente = tcp.accept()
  		file = open(outputFile, 'w')
  		print 'Conectado por', cliente

  		try:
  		
  			while True:
	  			cabecalho = con.recv(struct.calcsize('!8s 8s I I I I'))
	  			cabecalho_unpacked = struct.unpack('!8s 8s I I I I', cabecalho)
	  			tam = int(cabecalho_unpacked[3])
				dados = con.recv(struct.calcsize(str(tam)+'s'))
				dados_unpacked = struct.unpack(str(tam)+'s', dados)
		  		if (cabecalho_unpacked[4] != idPacoteAnterior): 
			  		file.write(dados_unpacked[0])
			  		length = 0
			  		flags = 128
			  		idPacoteAnterior = cabecalho_unpacked[4]
			  		chksumAnterior = cabecalho_unpacked[2]
			  		packAck = (cabecalho_unpacked[0], cabecalho_unpacked[0], cabecalho_unpacked[2], length, cabecalho_unpacked[4], flags)
			  		packAck_package = s_ack.pack(*packAck)
			  		con.send(packAck_package)
			  	if (cabecalho_unpacked[5] == 64):
			  		chksumAnterior = 0
					length = 0
					idPacoteAnterior = 1
					flags = 63
			  		break

		except Exception, e:
			
			print >> sys.stderr, "Exception: %s" % str(e)

  		finally:
    
			print 'Finalizando conexao do cliente', cliente	
		  	file.close()
		  	con.close()