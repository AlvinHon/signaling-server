del lambda_function.zip
del deployment_package.zip

7z -tzip a deployment_package.zip .\package\* -r
7z -tzip a lambda_function.zip lambda_function.py deployment_package.zip 