import argparse
from biokbase.CompressionBasedDistance.Helpers import get_url, set_url
from biokbase.CompressionBasedDistance.Client import CompressionBasedDistance, ServerError as CbdServerError

desc1 = '''
NAME
      cbd-url -- update or view url of the compression based distance service endpoint

SYNOPSIS      
'''

desc2 = '''
DESCRIPTION
      Display or set the URL endpoint for the compression based distance service.
      If run with no arguments or options, then the current URL is displayed.
      If run with a single argument, the current URL will be switched to the
      specified URL.  If the specified URL is named default, then the URL is
      reset to the default production URL.  When the --no-check optional
      argument is specified, the validity of the endpoint is not checked.
'''

desc3 = '''
EXAMPLES
      Display the current URL:
      > cbd-url
      Current URL: https://kbase.us/services/cbd/

      Use a new URL:
      > cbd-url http://localhost:7102
      New URL set to: http://localhost:7102

      Reset to the default URL:
      > cbd-url default
      New URL set to: https://kbase.us/services/cbd/

AUTHORS
      Mike Mundy
'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='cbd-url', epilog=desc3)
    parser.add_argument('-?', '--usage', help='show usage information', action='store_true', dest='usage')
    parser.add_argument('newurl', nargs='?', default=None, help='New URL endpoint')
    parser.add_argument('--no-check', help='do not check for a valid URL', action='store_true', dest='noCheck', default=False)
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()
    
    if args.usage:
        print usage
        exit(0)
        
    if args.newurl == None:
        url = get_url()
        print "Current URL: " + url
    else:
        url = set_url(args.newurl)
        print 'New URL set to: '+url
    if args.noCheck:
        exit(0)
    try:
        cbdClient = CompressionBasedDistance(url=url)
        serverInfo = cbdClient.version()
        if serverInfo[0] != 'CompressionBasedDistance':
            print url+' is not a compression-based distance server'
            exit(1)
        print url+' is valid and running %s v%s' %(serverInfo[0], serverInfo[1])
    except CbdServerError as e:
        print 'Endpoint at %s returned error: %s' %(url, e)
        exit(1)
    except Exception as e:
        print 'Could not get a valid response from endpoint at %s: %s' %(url, e)
        exit(1)
    exit(0)
