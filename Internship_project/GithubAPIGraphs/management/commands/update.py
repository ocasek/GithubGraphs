"""ADD funcition: at the end of the month check all websites and continue getting data"""

from django.core.management.base import BaseCommand, CommandError
from ...models import Website,Branche,PR,Issue
import dateutil.parser, json, requests
token="e714f655b28c07bec0ee3bbb4ebacc291de84c61"


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('website', type=str, nargs='?', default="")

    def request(self,web):
        _pr = PR.objects.filter(website=web).last()
        _issue = Issue.objects.filter(website=web).last()
        query_issue = ""
        query_pr = ""
        issue_cursor = ""
        pr_cursor = ""
        headers = {'Authorization': 'token ' + token}
        query = '''
               {
                 repository(owner:"''' + web.user + '''", name:"''' + web.repository + '''"){
                   issues(first: 100 states:CLOSED after:"''' + _issue.cursor + '''") {
                     edges {
                       cursor
                       node {
                     number
                     createdAt
                     state
                     title

                       }
                     }
                   }
                   pullRequests(first: 100 states:MERGED after:"''' + _pr.cursor + '''") {
                     edges {
                       cursor
                       node {
                         number
                         createdAt
                         state
                         title
                         closed
                         mergedAt
                         baseRefName
                         updatedAt
                       }
                     }
                 }
               }
               }
               '''
        r2 = requests.post('https://api.github.com/graphql', json.dumps({"query": query}),
                           headers=headers).json()
        pr_edges = r2['data']['repository']['pullRequests']['edges']
        issue_edges = r2['data']['repository']['issues']['edges']
        while pr_edges != [] or issue_edges != []:
            r2 = requests.post('https://api.github.com/graphql', json.dumps({"query": query}),
                               headers=headers).json()

            data = r2['data']['repository']
            if issue_edges != []:
                issue_edges = data['issues']['edges']
                for issue in data['issues']['edges']:
                    state = issue['node']['state']
                    number = issue['node']['number']
                    created_at = dateutil.parser.parse(issue['node']['createdAt'])
                    title = issue['node']['title']
                    issue_cursor = issue['cursor']
                    Issue(website=web, number=number,
                          created_at=created_at, state=state, title=title, cursor=issue_cursor).save()
                    print("ISSUE ", number)
                    query_issue = '''
                                            issues(first: 100 states:CLOSED after:"''' + issue_cursor + '''") {
                                                 edges {
                                                   cursor
                                                   node {
                                                 number
                                                 createdAt
                                                 state
                                                 title

                                                   }
                                                 }
                                               }'''
            if pr_edges != []:
                pr_edges = data['pullRequests']['edges']
                for pr in data['pullRequests']['edges']:
                    state = pr['node']['state']
                    number = pr['node']['number']
                    created_at = dateutil.parser.parse(pr['node']['createdAt'])
                    merged_at = dateutil.parser.parse(pr['node']['mergedAt'])
                    updated_at = dateutil.parser.parse(pr['node']['updatedAt'])
                    baseRefName = pr['node']['baseRefName']
                    title = pr['node']['title']
                    pr_cursor = pr['cursor']
                    PR(website=web, number=number, created_at=created_at,
                       state=state,
                       title=title, merged_at=merged_at, updated_at=updated_at, cursor=pr_cursor,
                       branche=Branche.objects.get_or_create(baseRefName=baseRefName,
                                                             website=web)[0]).save()
                    print("PR ", number)
                    query_pr = '''
                                pullRequests(first: 100 states:MERGED after:"''' + pr_cursor + '''") {
                                         edges {
                                           cursor
                                           node {
                                         number
                                         createdAt
                                         state
                                         title
                                         closed
                                         mergedAt
                                         baseRefName
                                         updatedAt
                                           }
                                         }
                                     }'''
            query = '''
                   {
                     repository(owner:"''' + web.user + '''", name:"''' + web.repository + '''"){
                       ''' + query_issue + '''
                       ''' + query_pr + '''

                    }
                   }
                   '''
    def handle(self, *args, **options):
        _website = options.get('website', None)

        if _website=="":
            for web in Website.objects.all():
                print(web)
                self.request(web)
        else:
            try:
                web=Website.objects.get(user= _website.split("/")[0],repository=_website.split("/")[1])
                self.request(web)
            except Exception as e:
                print("Invalid repository")