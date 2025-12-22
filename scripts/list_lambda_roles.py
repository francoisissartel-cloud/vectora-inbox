#!/usr/bin/env python3
"""
Script pour lister les rôles IAM existants
"""
import boto3
from botocore.exceptions import ClientError

def list_lambda_roles():
    """Liste les rôles IAM qui peuvent être utilisés pour Lambda"""
    
    iam = boto3.client('iam')
    
    try:
        # Lister tous les rôles
        paginator = iam.get_paginator('list_roles')
        
        lambda_roles = []
        
        for page in paginator.paginate():
            for role in page['Roles']:
                role_name = role['RoleName']
                
                # Filtrer les rôles qui semblent être pour Lambda
                if any(keyword in role_name.lower() for keyword in ['lambda', 'vectora', 'inbox']):
                    lambda_roles.append({
                        'name': role_name,
                        'arn': role['Arn'],
                        'created': role['CreateDate']
                    })
        
        print("[LAMBDA ROLES FOUND]")
        for role in lambda_roles:
            print(f"  - {role['name']}")
            print(f"    ARN: {role['arn']}")
            print(f"    Created: {role['created']}")
            print()
        
        return lambda_roles
        
    except ClientError as e:
        print(f"[ERROR] Failed to list roles: {e}")
        return []

if __name__ == "__main__":
    roles = list_lambda_roles()
    
    if roles:
        print(f"[INFO] Found {len(roles)} potential Lambda roles")
    else:
        print("[WARNING] No Lambda roles found")