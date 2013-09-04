import argparse
from biokbase.CompressionBasedDistance.Helpers import get_url, set_url

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
      reset to the default production URL.
'''

desc3 = '''
EXAMPLES
      Display the current URL:
      > cbd-url
      Current URL: http://kbase.us/services/CompressionBasedDistance

      Use a new URL:
      > cbd-url http://localhost:7102
      New URL set to: http://localhost:7102

      Reset to the default URL:
      > cbd-url default
      New URL set to: http://kbase.us/services/CompressionBasedDistance/

AUTHORS
      Mike Mundy
'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, prog='cbd_url', epilog=desc3)
    parser.add_argument('-?', '--usage', help='show usage information', action='store_true', dest='usage')
    parser.add_argument('newurl', nargs='?', default=None, help='New URL endpoint')
    usage = parser.format_usage()
    parser.description = desc1 + '      ' + usage + desc2
    parser.usage = argparse.SUPPRESS
    args = parser.parse_args()
    
    if args.usage:
        print usage
        exit(0)
        
    if args.newurl == None:
        print "Current URL: " + get_url()
    else:
        print "New URL set to: " + set_url(args.newurl)
    exit(0)
    