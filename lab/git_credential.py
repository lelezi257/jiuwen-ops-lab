"""git credential helper: credentials go only to git's private pipe."""
import sys
from lab.common import secret
if len(sys.argv)>1 and sys.argv[1]=='get':
 fields=dict(line.rstrip('\n').split('=',1) for line in sys.stdin if '=' in line)
 if fields.get('host')=='github.com':print('username=x-access-token\npassword='+secret('github_token')+'\n')
