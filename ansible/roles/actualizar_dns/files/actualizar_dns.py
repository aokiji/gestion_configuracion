import urllib2
import urllib
import pycurl
import gzip
import logging
import logging.handlers
import sys
import re
from bs4 import BeautifulSoup

try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO

class Site5DnsManager:
    '''
    Con esta clase manejamos el acceso a Site5
    '''
    TIMEOUT = 100
    USUARIO_POR_DEFECTO = "usuario"
    PASSWORD_POR_DEFECTO = "password"
    DOMINIO = 'multiservicioselmorche.es'
    
    def __init__(self, debug = False):
        '''
        Constructor
        '''
        self.curl = pycurl.Curl()
        self.headers = {}
        self.debug = debug
        
        # configuramos el log
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler(stream=sys.stdout)
        handler.setFormatter(logging.Formatter(fmt='%(asctime)-15s %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def BackstageLogin(self,usuario=USUARIO_POR_DEFECTO, password=PASSWORD_POR_DEFECTO):
        '''
        Se loguea en el backstage de site5
        '''
        self.logger.info("Procedemos a hacer login con el usuario %(usuario)s", {'usuario': usuario})
        buff = BytesIO()
        self.curl.setopt(pycurl.TIMEOUT, Site5DnsManager.TIMEOUT)
        self.curl.setopt(pycurl.FOLLOWLOCATION, True)
        self.curl.setopt(pycurl.URL, 'https://backstage.site5.com/client/auth/login')
        self.curl.setopt(pycurl.HTTPHEADER, [
                                      'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
                                      'Accept-Encoding: gzip, deflate', 
                                      'Accept-Language: en-US,en;q=0.5',
                                      'Connection: keep-alive',
                                      'Host: backstage.site5.com',
                                      'Referer: https://backstage.site5.com/client/auth/login',
                                      'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0',
                                      'Content-Type: application/x-www-form-urlencoded'])
        self.curl.setopt(pycurl.POST, True)
        self.curl.setopt(pycurl.POSTFIELDS, urllib.urlencode({'user_login':usuario, 'user_password': Site5DnsManager.PASSWORD_POR_DEFECTO, 'commit': 'Login'}))
        if self.debug:
            self.curl.setopt(pycurl.VERBOSE, True)
        self.curl.setopt(pycurl.HEADERFUNCTION, self.__parse_header__)
        self.curl.setopt(pycurl.COOKIEFILE, "") # activamos cookies
        self.curl.setopt(pycurl.WRITEDATA, buff)
        self.curl.perform()
        self.curl.reset()
        
        self.logger.info("--> Respuesta recibida con codigo %d", self.curl.getinfo(self.curl.RESPONSE_CODE))
        
        if self.debug:
            buff.seek(0)
            
            if 'content-encoding' in self.headers and self.headers['content-encoding'] == 'gzip':
                fgzip = gzip.GzipFile(fileobj=buff)
                print fgzip.read()
            else:
                print buff.read()
                
    def ObtenerLinea(self, host):
        '''
        '''
        self.logger.info("Intentando averiguar la linea para %(host)s", {'host': host})
        buff = BytesIO()
        self.curl.setopt(pycurl.TIMEOUT, Site5DnsManager.TIMEOUT)
        self.curl.setopt(pycurl.FOLLOWLOCATION, True)
        self.curl.setopt(pycurl.URL, 'https://proxy-netadmin-424377.backstage.site5.com/frontend/sa2/zoneedit/ajax/list-zone-records.live.php')
        self.curl.setopt(pycurl.HTTPHEADER, [
                              'Accept: Accept: text/javascript, text/html, application/xml, text/xml, */*', 
                              'Accept-Encoding: gzip, deflate', 
                              'Accept-Language: en-US,en;q=0.5',
                              'Connection: keep-alive',
                              'X-Requested-With: XMLHttpRequest',
                              'X-Prototype-Version: 1.7',
                              'Host: proxy-netadmin-424377.backstage.site5.com',
                              'Referer: https://proxy-netadmin-424377.backstage.site5.com/frontend/sa2/zoneedit/simple.php',
                              'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0',])
        self.curl.setopt(pycurl.POST, True)
        self.curl.setopt(pycurl.POSTFIELDS, urllib.urlencode({'domain':Site5DnsManager.DOMINIO, 'cachefix': '1430170127276'}))
        if self.debug:
            self.curl.setopt(pycurl.VERBOSE, True)
        self.curl.setopt(pycurl.HEADERFUNCTION, self.__parse_header__)
        self.curl.setopt(pycurl.COOKIEFILE, "") # activamos cookies
        self.curl.setopt(pycurl.WRITEDATA, buff)
        self.curl.perform()
        self.curl.reset()
        
        self.logger.info("--> Respuesta recibida con codigo %d", self.curl.getinfo(self.curl.RESPONSE_CODE))
        
        
        buff.seek(0)           
        if 'content-encoding' in self.headers and self.headers['content-encoding'] == 'gzip':
            fgzip = gzip.GzipFile(fileobj=buff)
            html=fgzip.read()
        else:
            html=buff.read()
            
        soup = BeautifulSoup(html)
        resultado = soup.find('td', class_ ='recordName', text = re.compile(host));
        if resultado is None:
            self.logger.error("No se pudo encontrar la linea correspondiente para el host")
            raise Exception("No se pudo encontrar la linea correspondiente para el host")
        linea = resultado.parent.find('span', class_='lineNumber')
        if linea is None:
            self.logger.error("No se pudo encontrar la linea correspondiente para el host, error al parsear el documento")
            raise Exception("No se pudo encontrar la linea correspondiente para el host, error al parsear el documento")
        
        linea = int(linea.get_text())
        self.logger.info("Encontrada linea %(linea)d", {'linea': linea});
        return linea
        
    def ActualizarIp(self, ip, host):
        '''
        Actualiza la ip
        '''
        #linea = self.ObtenerLinea(host)
        linea = 21
        
        self.logger.info("Intentamos actualizar la ip del host %(host)s --> %(ip)s", {'host': host, 'ip': ip})
        buff = BytesIO()
        self.headers = {}
        self.curl.setopt(pycurl.TIMEOUT, Site5DnsManager.TIMEOUT)
        self.curl.setopt(pycurl.FOLLOWLOCATION, 1)
        self.curl.setopt(pycurl.URL, 'https://proxy-netadmin-424377.backstage.site5.com/json-api/cpanel?cachefix=1418987022527')
        self.curl.setopt(pycurl.HTTPHEADER, [
                              'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
                              'Accept-Encoding: gzip, deflate', 
                              'Accept-Language: en-US,en;q=0.5',
                              'Connection: keep-alive',
                              'X-Requested-With: XMLHttpRequest',
                              'X-Prototype-Version: 1.7.1',
                              'Host: proxy-netadmin-424377.backstage.site5.com',
                              'Referer: https://proxy-netadmin-424377.backstage.site5.com/frontend/sa2/zoneedit/ajax/edit-record.modal.html?domain=multiservicioselmorche.es&line={}&type=A&recordname={}.&recordip={}'.format(linea, host,ip),
                              'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:34.0) Gecko/20100101 Firefox/34.0',
                              'Content-Type: application/x-www-form-urlencoded; charset=UTF-8',
                              'Pragma: no-cache',
                              'Cache-Control: no-cache'])
        self.curl.setopt(pycurl.POST, True)
        self.curl.setopt(pycurl.POSTFIELDS, urllib.urlencode({
                                                              'domain': Site5DnsManager.DOMINIO, 
                                                              'Line': linea, 
                                                              'address': ip, 
                                                              'type': 'A', 
                                                              'cpanel_jsonapi_module': 'ZoneEdit',
                                                              'cpanel_jsonapi_func': 'edit_zone_record',
                                                              'cpanel_jsonapi_apiversion': '2'}))
        if self.debug:
            self.curl.setopt(pycurl.VERBOSE, True)
        self.curl.setopt(pycurl.HEADERFUNCTION, self.__parse_header__)
        self.curl.setopt(pycurl.COOKIEFILE, "") # activamos cookies
        self.curl.setopt(pycurl.WRITEDATA, buff)
        self.curl.perform()
        self.curl.reset()
        
        self.logger.info("--> Respuesta recibida con codigo %d", self.curl.getinfo(self.curl.RESPONSE_CODE))
        
        if self.debug:
            buff.seek(0)
            
            if 'content-encoding' in self.headers and self.headers['content-encoding'] == 'gzip':
                fgzip = gzip.GzipFile(fileobj=buff)
                print fgzip.read()
            else:
                print buff.read()
       
    def __parse_header__(self, header_line):
        # HTTP standard specifies that headers are encoded in iso-8859-1.
        # On Python 2, decoding step can be skipped.
        # On Python 3, decoding step is required.
        header_line = header_line.decode('iso-8859-1')
    
        # Header lines include the first status line (HTTP/1.x ...).
        # We are going to ignore all lines that don't have a colon in them.
        # This will botch headers that are split on multiple lines...
        if ':' not in header_line:
            return
    
        # Break the header line into header name and value.
        name, value = header_line.split(':', 1)
    
        # Remove whitespace that may be present.
        # Header lines include the trailing newline, and there may be whitespace
        # around the colon.
        name = name.strip()
        value = value.strip()
    
        # Header names are case insensitive.
        # Lowercase name here.
        name = name.lower()
    
        # Now we can actually record the header name and value.
        self.headers[name] = value


    def __enter__(self):
        return self


    def __exit__(self, tipo, value, traceback):
        self.curl.close()

def ObtenerIp():
    '''
    Recupera la ip externa
    '''
    ip_str = urllib2.urlopen("http://ipinfo.io/ip").read()
    return ip_str.rstrip()

    
def main():
    with Site5DnsManager(debug=False) as site5_dns:
        site5_dns.BackstageLogin()
        site5_dns.ActualizarIp(ip=ObtenerIp(), host='nico.multiservicioselmorche.es')

if __name__ == "__main__":
    main()