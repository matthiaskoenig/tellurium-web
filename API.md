# REST API
TODO: describe urls and API in a few words
TODO: example in python `docs/api.ipynb`


The Rest Api access the archives, tags and users of Tellurium. 

##Browsable User Interface (urls)
* API schema (.../api/)
* hyperlinked list of archives  and create new archive <sup>[1](#myfootnote1)</sup>
 (.../api/archives/)  *(filters)* 
* specific archive (.../api/archives/{uuid})  *(filters)*
* hyperlinked list of tags (.../api/tags/) *(filters)*
* specific tag (.../api/tags/{uuid})  *(filters)*
* hyperlinked list of users (.../api/users/) *(filters, search <sup>[2](#myfootnote2)</sup>)*.
* specific user (.../api/users/{id})  *(filters, search)*


*<a name="myfootnote1">1</a>: A new archive automatically linked to the current user.* 
*<a name="myfootnote1">2</a>: searches in.*

##API Client in Python
How to access the the (core) api in python is demonstrated in a notebook in the docs (/docs/api.ipynb).
###Installation:
```
$ pip install coreapi
```
###Quickstart:
```
auth = coreapi.auth.BasicAuthentication(
    username='janek89',
    password='test'
    )
client = coreapi.Client(auth=auth)
document = client.get("http://127.0.0.1:8001/api/")

```
### Example:
search in archives for `sbml`.
```angular2html
data = client.action(document,["archives", "list"], params={"search":"sbml"} )

#print(json.dumps(data,indent=4))
```



 
