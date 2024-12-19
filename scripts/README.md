# How to Run Scripts

In order to be able to run the scripts in this directory, you need to have logged into Azure using `azure login`. This used to be a script, but since "az login" is interactive it the current version, we will run this manually.

```
# Login
az login
```

If will ask you to select a subscription like this:

```
Retrieving tenants and subscriptions for the selection...

[Tenant and subscription selection]

No     Subscription name                     Subscription ID                       Tenant
-----  ------------------------------------  ------------------------------------  ---------
[1]    Azure for Students <UUID>  KamIT 365
[2] *  IaC Terraform      <UUID>  KamIT 365
[3]    Lorem Ipsum        <UUID>  KamIT 365
[4]    KAMK VDI           <UUID>  KamIT 365
```

Choose the one you want by typing the number and pressing enter.