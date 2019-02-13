from github import Github

g = Github('91e299613b59fe50950fb110d079c2b7f39c70f8')

# for repo in g.get_user().get_repos():
#     print(repo.name)

# repo = g.get_repo("rails/rails")
# for pr in repo.get_pulls(35249):
#     # You can access pulls
#     print(pr)

repo = g.get_repo("rails/rails")
pr = repo.get_pull(35249)
print(pr.state)
files = pr.get_files()
for file in files:
    print(file.filename)