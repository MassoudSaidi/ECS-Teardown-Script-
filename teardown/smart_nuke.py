import boto3
import time
import os
import argparse
import json
import subprocess

# ... [All other functions like get_boto_clients, delete_ecs_service, etc. are the same] ...
# ... [For brevity, only the new function and the updated main block are shown] ...

def get_boto_clients(region):
    return {
        'ecs': boto3.client('ecs', region_name=region),
        'ec2': boto3.client('ec2', region_name=region),
        'autoscaling': boto3.client('autoscaling', region_name=region),
        'elbv2': boto3.client('elbv2', region_name=region),
        'iam': boto3.client('iam', region_name=region),
    }

def delete_ecs_service(clients, config):
    print(f"--- Handling ECS Service: {config['SERVICE_NAME']} in cluster {config['CLUSTER_NAME']} ---")
    try:
        # Check if the cluster exists first
        clients['ecs'].describe_clusters(clusters=[config['CLUSTER_NAME']])
        print(f"Scaling down service {config['SERVICE_NAME']} to 0 desired tasks...")
        clients['ecs'].update_service(cluster=config['CLUSTER_NAME'], service=config['SERVICE_NAME'], desiredCount=0)
        waiter = clients['ecs'].get_waiter('services_stable')
        waiter.wait(cluster=config['CLUSTER_NAME'], services=[config['SERVICE_NAME']], WaiterConfig={'Delay': 15, 'MaxAttempts': 40})
        print("Service scaled down successfully.")
        clients['ecs'].delete_service(cluster=config['CLUSTER_NAME'], service=config['SERVICE_NAME'], force=True)
        print(f"Service {config['SERVICE_NAME']} deleted successfully.")
    except clients['ecs'].exceptions.ClusterNotFoundException:
        print(f"Cluster {config['CLUSTER_NAME']} not found, cannot delete service. Skipping.")
    except clients['ecs'].exceptions.ServiceNotFoundException:
        print(f"Service {config['SERVICE_NAME']} not found. Skipping.")
    except Exception as e:
        print(f"An error occurred while deleting ECS service: {e}")

# ... [All other deletion functions remain the same] ...

def delete_ecs_cluster(clients, config):
    print(f"--- Deleting ECS Cluster: {config['CLUSTER_NAME']} ---")
    try:
        clients['ecs'].delete_cluster(cluster=config['CLUSTER_NAME'])
        waiter = clients['ecs'].get_waiter('clusters_inactive')
        waiter.wait(clusters=[config['CLUSTER_NAME']], WaiterConfig={'Delay': 15, 'MaxAttempts': 40})
        print(f"Cluster {config['CLUSTER_NAME']} deleted successfully.")
    except clients['ecs'].exceptions.ClusterNotFoundException:
        print(f"Cluster {config['CLUSTER_NAME']} not found. Skipping.")
    except Exception as e:
        print(f"An error occurred while deleting ECS cluster: {e}")

def delete_autoscaling_group_and_instances(clients, config):
    print(f"--- Handling Auto Scaling Group starting with: {config['ASG_NAME_PREFIX']} ---")
    try:
        response = clients['autoscaling'].describe_auto_scaling_groups()
        asg_details = next((asg for asg in response['AutoScalingGroups'] if asg['AutoScalingGroupName'].startswith(config['ASG_NAME_PREFIX'])), None)
        if not asg_details:
            print("No matching Auto Scaling Group found. Skipping.")
            return
        asg_name = asg_details['AutoScalingGroupName']
        print(f"Found ASG: {asg_name}. Setting min/max/desired to 0...")
        clients['autoscaling'].update_auto_scaling_group(
            AutoScalingGroupName=asg_name, MinSize=0, MaxSize=0, DesiredCapacity=0
        )
        time.sleep(10)
        print("Checking for instances in 'Terminating:Wait' state...")
        while True:
            asg_desc = clients['autoscaling'].describe_auto_scaling_groups(AutoScalingGroupNames=[asg_name])['AutoScalingGroups'][0]
            instances = asg_desc.get('Instances', [])
            if not instances:
                print("All instances have been terminated.")
                break
            print(f"Found {len(instances)} instance(s). Checking their state...")
            for instance in instances:
                if instance.get('LifecycleState') == 'Terminating:Wait':
                    instance_id = instance['InstanceId']
                    print(f"Instance {instance_id} is in 'Terminating:Wait'. Completing lifecycle action...")
                    hook_response = clients['autoscaling'].describe_lifecycle_hooks(AutoScalingGroupName=asg_name)
                    lifecycle_hook_name = hook_response['LifecycleHooks'][0]['LifecycleHookName'] if hook_response['LifecycleHooks'] else None
                    if lifecycle_hook_name:
                        clients['autoscaling'].complete_lifecycle_action(
                            LifecycleHookName=lifecycle_hook_name,
                            AutoScalingGroupName=asg_name,
                            LifecycleActionResult='CONTINUE',
                            InstanceId=instance_id
                        )
                        print(f"Lifecycle action for {instance_id} completed. It will now terminate.")
                    else:
                        print(f"Warning: Could not find a lifecycle hook for ASG {asg_name} to complete.")
            print("Waiting for 15 seconds before checking again...")
            time.sleep(15)
        print("All instances terminated from ASG. Deleting the group...")
        clients['autoscaling'].delete_auto_scaling_group(AutoScalingGroupName=asg_name, ForceDelete=True)
        print(f"Auto Scaling Group {asg_name} deleted successfully.")
    except Exception as e:
        print(f"An error occurred during ASG deletion: {e}")

def delete_launch_template(clients, config):
    print(f"--- Deleting Launch Templates starting with: {config['LAUNCH_TEMPLATE_PREFIX']} ---")
    try:
        response = clients['ec2'].describe_launch_templates()
        for lt in response['LaunchTemplates']:
            if lt['LaunchTemplateName'].startswith(config['LAUNCH_TEMPLATE_PREFIX']):
                print(f"Deleting Launch Template: {lt['LaunchTemplateName']} ({lt['LaunchTemplateId']})")
                clients['ec2'].delete_launch_template(LaunchTemplateId=lt['LaunchTemplateId'])
    except Exception as e:
        print(f"An error occurred: {e}")

def delete_load_balancer_and_target_group(clients, config):
    print(f"--- Handling Load Balancer and Target Group ---")
    try:
        response = clients['elbv2'].describe_load_balancers(Names=[config['ALB_NAME']])
        lb_arn = response['LoadBalancers'][0]['LoadBalancerArn']
        print(f"Deleting Load Balancer: {config['ALB_NAME']} ({lb_arn})")
        clients['elbv2'].delete_load_balancer(LoadBalancerArn=lb_arn)
        waiter = clients['elbv2'].get_waiter('load_balancers_deleted')
        waiter.wait(LoadBalancerArns=[lb_arn])
        print("Load Balancer deleted successfully.")
    except clients['elbv2'].exceptions.LoadBalancerNotFoundException:
        print(f"Load Balancer {config['ALB_NAME']} not found. Skipping.")
    except Exception as e:
        print(f"An error occurred deleting LB: {e}")
    try:
        response = clients['elbv2'].describe_target_groups(Names=[config['TARGET_GROUP_NAME']])
        tg_arn = response['TargetGroups'][0]['TargetGroupArn']
        print(f"Deleting Target Group: {config['TARGET_GROUP_NAME']} ({tg_arn})")
        clients['elbv2'].delete_target_group(TargetGroupArn=tg_arn)
        print("Target Group deleted successfully.")
    except clients['elbv2'].exceptions.TargetGroupNotFoundException:
        print(f"Target Group {config['TARGET_GROUP_NAME']} not found. Skipping.")
    except Exception as e:
        print(f"An error occurred deleting TG: {e}")

def delete_security_groups(clients, vpc_id, config):
    print(f"--- Deleting Security Groups in VPC {vpc_id} ---")
    sg_names = [config['ALB_SG_NAME'], config['ECS_SG_NAME']]
    for sg_name in sg_names:
        try:
            response = clients['ec2'].describe_security_groups(
                Filters=[{'Name': 'group-name', 'Values': [sg_name]}, {'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            if response['SecurityGroups']:
                sg_id = response['SecurityGroups'][0]['GroupId']
                print(f"Deleting Security Group: {sg_name} ({sg_id})")
                time.sleep(5)
                clients['ec2'].delete_security_group(GroupId=sg_id)
            else:
                print(f"Security Group {sg_name} not found.")
        except Exception as e:
            print(f"Could not delete SG {sg_name}. It might be in use or already gone. Error: {e}")

def get_vpc_id_by_name(clients, name):
    vpcs = clients['ec2'].describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [name]}])['Vpcs']
    if vpcs: return vpcs[0]['VpcId']
    return None

# ######################################################
# #          NEW FUNCTION TO DELETE CAPACITY PROVIDER    #
# ######################################################

def delete_capacity_providers(clients, config):
    """
    Finds and deletes the specific ECS Capacity Provider.
    This runs after the ASG is deleted, so it should not be in use.
    """
    cp_name = config.get('CAPACITY_PROVIDER_NAME')
    if not cp_name:
        print("--- No Capacity Provider Name found in config, skipping deletion ---")
        return
        
    print(f"--- Handling ECS Capacity Provider: {cp_name} ---")
    try:
        # First, we need to ensure it's not associated with any cluster.
        # This should already be true if the cluster is being deleted, but we'll be defensive.
        clusters_response = clients['ecs'].describe_clusters(clusters=[config['CLUSTER_NAME']])
        if clusters_response.get('clusters'):
            cluster_arn = clusters_response['clusters'][0]['clusterArn']
            print(f"Disassociating capacity provider from cluster {config['CLUSTER_NAME']} if necessary...")
            clients['ecs'].put_cluster_capacity_providers(
                cluster=config['CLUSTER_NAME'],
                capacityProviders=[], # Disassociate all
                defaultCapacityProviderStrategy=[]
            )
            time.sleep(5) # Give a moment for disassociation

        # Now, delete the capacity provider itself
        print(f"Deleting capacity provider {cp_name}...")
        clients['ecs'].delete_capacity_provider(capacityProvider=cp_name)
        print(f"Capacity Provider {cp_name} deleted successfully.")

    except clients['ecs'].exceptions.ClusterNotFoundException:
        # If the cluster is already gone, we can just delete the provider.
        try:
            print(f"Cluster not found. Attempting direct deletion of capacity provider {cp_name}...")
            clients['ecs'].delete_capacity_provider(capacityProvider=cp_name)
            print(f"Capacity Provider {cp_name} deleted successfully.")
        except Exception as e:
            print(f"An error occurred during direct deletion of capacity provider: {e}")
    except Exception as e:
        print(f"An error occurred deleting capacity provider: {e}")


def get_config_from_terraform_onlyTerraform(folder_path):
    print(f"--- Getting configuration from Terraform output in: {folder_path} ---")
    try:
        print("Running 'terraform init'...")
        subprocess.run(
            ["terraform", "init", "-upgrade"],
            cwd=folder_path,
            capture_output=True, text=True, check=True
        )
        print("Running 'terraform output -json nuke_script_config'...")
        process = subprocess.run(
            ["terraform", "output", "-json", "nuke_script_config"],
            cwd=folder_path,
            capture_output=True, text=True, check=True
        )
        config = json.loads(process.stdout)
        return config
    except FileNotFoundError:
        print("\nFATAL: 'terraform' command not found.")
        print("Please ensure Terraform is installed and in your system's PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print("\nFATAL: A Terraform command failed.")
        print(f"Return Code: {e.returncode}")
        print("\n----- Terraform STDERR -----")
        print(e.stderr)
        print("--------------------------")
        return None
    except Exception as e:
        print(f"\nFATAL: An unexpected error occurred. {e}")
        return None


def get_config_from_terraform(folder_path):
    """
    Runs 'terragrunt output' in a specific environment directory to get
    resource names in a reliable JSON format.
    """
    print(f"--- Getting configuration from Terragrunt output in: {folder_path} ---")
    try:
        # Step 1: Run 'terragrunt output' command.
        # Terragrunt automatically handles the 'init' process.
        # We target the specific output block from our module's outputs.tf
        print(f"Running 'terragrunt output -json nuke_script_config' in {folder_path}...")
        
        # We now use 'terragrunt' instead of 'terraform'
        process = subprocess.run(
            ["terragrunt", "output", "-json", "nuke_script_config"],
            cwd=folder_path,
            capture_output=True, text=True, check=True
        )
        
        # The output from terragrunt is the same JSON string, load it
        config = json.loads(process.stdout)
        return config

    except FileNotFoundError:
        print("\nFATAL: 'terragrunt' command not found.")
        print("Please ensure Terragrunt is installed and in your system's PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print("\nFATAL: A Terragrunt command failed.")
        print(f"Return Code: {e.returncode}")
        print("\n----- Terragrunt STDERR -----")
        print(e.stderr)
        print("-----------------------------")
        print("Please ensure you have run 'terragrunt apply' successfully for this environment at least once.")
        return None
    except Exception as e:
        print(f"\nFATAL: An unexpected error occurred. {e}")
        return None



# ##################################################################
# #                     MAIN EXECUTION BLOCK (Updated)             #
# ##################################################################

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Programmatically destroy AWS resources defined in a Terraform project.")
    parser.add_argument("path", help="The absolute or relative path to the directory containing your Terraform project.")
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        print(f"Error: The provided path '{args.path}' is not a valid directory.")
        exit(1)

    config = get_config_from_terraform(args.path)
    if not config:
        print("\nAborting due to configuration errors.")
        exit(1)

    # Add the capacity provider name to the config dictionary for the new function
    # This assumes the name is derivable from your locals.tf, which it is.
    config['CAPACITY_PROVIDER_NAME'] = f"{config.get('PROJECT_NAME', 'btap-app')}-{config.get('ENVIRONMENT', 'dev')}-capacity-provider"
    
    print("\n>>> Discovered Configuration <<<")
    print(json.dumps(config, indent=2))
    input("\n>>> Press Enter to continue with the destruction of the above resources, or Ctrl+C to abort. <<<")

    clients = get_boto_clients(config['AWS_REGION'])
    
    print("\n>>> Starting AWS Resource Destruction Script <<<")
    # Deletion order is critical
    delete_ecs_service(clients, config)
    delete_autoscaling_group_and_instances(clients, config)
    delete_load_balancer_and_target_group(clients, config)
    delete_launch_template(clients, config)
    
    # NEW: Delete the Capacity Provider *after* its dependencies (ASG, Service) are gone.
    delete_capacity_providers(clients, config)
    
    delete_ecs_cluster(clients, config)
    
    print("\n--- SKIPPING IAM ROLE DELETION BY DEFAULT ---")
    
    vpc_id = get_vpc_id_by_name(clients, config['VPC_NAME'])
    if vpc_id:
        print("\nWaiting 60 seconds for network interfaces to detach before deleting security groups...")
        time.sleep(60)
        delete_security_groups(clients, vpc_id, config)
    else:
        print(f"\nCould not find VPC with name {config['VPC_NAME']} to delete SGs from.")
        
    print("\n>>> Destruction Script Finished <<<")
    print("NOTE: This script does not delete the VPC or IAM Roles.")
    print("You can run 'terragrunt destroy' now to safely remove any remaining resources.")