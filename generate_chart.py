import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sqlalchemy import MetaData, Table, Column, Integer, String, LargeBinary
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
import os
import paramiko
import subprocess

metadata = MetaData()

class Image(Base):
    __tablename__ = 'Ivdda_Images'
    image_id = Column(Integer, primary_key=True, autoincrement=True)
    image_name = Column(String(255), nullable=False)
    image_data = Column(LargeBinary, nullable=False)


def gen_xo_chart(table_name: str, db_session: Session):
    # hp values to filter on
    hp_values = [1]

    # Step 1: Fetch data from the Ivdda table
    ivdda_table = Table(table_name, metadata, autoload_with=engine)
    query = db_session.query(ivdda_table).all()
    ivdda_data = pd.DataFrame(query, columns=[col.name for col in ivdda_table.columns])

    # Step 2: Fetch the compliance matrix data
    compliance_data = _fetch_compliance_matrix(db_session)

    # Step 3: Filter the compliance matrix for the relevant symbol (i.e., the table name 'Ivdda')
    compliance_data = compliance_data[compliance_data['Symbol'] == table_name]

    # Step 4: Ensure necessary columns are available in the Ivdda table
    if table_name == 'Ivdda0v9_tx_master':
        ivdda = "Ivdda0v9_tx_master"
        required_columns = ['Sample', 'Temp', 'Vdda', 'hp<1:0>', 'Ivdda0v9_tx_master']
    
    ivdda_data["hp<1:0>"] = (
        pd.to_numeric(ivdda_data["hp<1:0>"], errors="coerce").fillna(-1).astype(int)
    )

    # Step 6: Merge Ivdda data with the ComplianceMatrix based on hp<1:0> (Condition in ComplianceMatrix)
    ivdda_data = ivdda_data.merge(
        compliance_data,
        how='left',
        left_on='hp<1:0>',
        right_on='Condition'
    )

    # Step 7: Prepare project titles and filter data by sample
    project_titles = ivdda_data['Sample'].unique().tolist()  # Get unique samples as project titles
    project_dataframes = [ivdda_data[ivdda_data['Sample'] == sample] for sample in
                            project_titles]  # Filter data by sample

    # Add charts for each hp value
    for hp_value in hp_values:
        _add_chart_with_dynamic_sample(
           hp_value, project_dataframes, project_titles, ivdda
        )


def save_images_to_server(images, local_dir, remote_user, remote_host, remote_dir, password:str):
    # Save images to local directory
    for image in images:
        local_path = os.path.join(local_dir, f"{image.image_name}.jpg")
        with open(local_path, 'wb') as file:
            file.write(image.image_data)

    # Initialize SSH client
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Connect to the remote server
    print(f"\nConnecting to {remote_host}...")
    ssh.connect(remote_host, username=remote_user, password=password)
    
    # Initialize SFTP client
    sftp = ssh.open_sftp()

    home_dir = "/home/nxg08329/XO_images/"

    # Transfer files to remote server home path
    for image in images:
        image_name = f"{image.image_name}.jpg"
        local_path = os.path.join(local_dir, image_name)
        home_path = os.path.join(home_dir, image_name)

        # Copy image to remote home directory
        scp_command_to_user_home = f"scp {local_path} {remote_user}@{remote_host}:{home_path}"
        result = subprocess.run(scp_command_to_user_home, shell=True, capture_output=True, text=True)
        # Check if the command was successful
        if result.returncode == 0:
            print(f"\n{image.image_name}.jpg transferred successfully to {remote_user} home directory.")
        else:
            print(f"Error occurred: {result.stderr}")
    
    files = sftp.listdir(home_dir)

    # Now use SSH to run the sudo command to move the files to /var
    for file in files:
        temp_file = home_dir + file
        destination_file = remote_dir + file
        sudo_command = f"sudo mv {temp_file} {destination_file}"

        # Execute the sudo command to move the file
        stdin, stdout, stderr = ssh.exec_command(sudo_command, get_pty=True)

        # Provide the password for sudo
        stdin.write(password + '\n')
        stdin.flush()

        # Check for errors
        error = stderr.read().decode()
        if error:
            print(f"\nError occurred while moving file {file}: {error}")
        else:
            print(f"\nSuccessfully moved {file} to {destination_file}")

    # Close the SFTP session and SSH connection
    sftp.close()
    ssh.close()

    print("\nFile copy completed successfully.")


def insert_image(image_path, image_name):
    # Read the image file
    with open(image_path, 'rb') as file:
        binary_data = file.read()
    
    # Create an Image object
    new_image = Image(image_name=image_name, image_data=binary_data)
    
    # Add the image to the session and commit
    db_session.add(new_image)
    db_session.commit()


def gen_report():
    """
    Generate Ivdda reports by extracting data from a given database table,
    processing it, and generate a chart out of the measurement data
    """
    modules = ["Ivdda0v9_tx_master"]
    global db_session
    db_session = SessionLocal()

    for table_name in modules:
        if table_name == "Ivdda0v9_tx_master":
            gen_xo_chart(table_name=table_name, db_session=db_session)

    # Local directory containing images
    local_directory = "scripts/images"

    # Iterate over each file in the local directory and insert image into IMAGES Table
    for filename in os.listdir(local_directory):
        images = db_session.query(Image).filter(Image.image_name == os.path.splitext(os.path.basename(filename))[0])
        if images.count() == 0: 
            insert_image(os.path.join(local_directory, filename), os.path.splitext(os.path.basename(filename))[0])

    images = db_session.query(Image).all()
    
    remote_user = "nxg08329"
    remote_host = "10.168.2.129"
    remote_dir = "/var/www/system_validation/XO_images/"
    password = "pr8!@VR6"

    # Save images to server
    save_images_to_server(images, local_directory, remote_user, remote_host, remote_dir, password)


def _fetch_compliance_matrix(db_session: Session) -> pd.DataFrame:
    """Fetch the compliance matrix from the database."""
    compliance_table = Table("ComplianceMatrix", metadata, autoload_with=engine)
    query = db_session.query(compliance_table).all()
    compliance_data = pd.DataFrame(
        query, columns=[col.name for col in compliance_table.columns]
    )

    # Ensure 'Condition' column is numeric (same type as 'gm<2:0>')
    compliance_data["Condition"] = pd.to_numeric(
        compliance_data["Condition"], errors="coerce"
    )
    return compliance_data


def _add_chart_with_dynamic_sample(hp_value, dfs: pd.DataFrame, project_titles, ivdda):
    rows = []
    filtered_dataframes = [
        df[df["hp<1:0>"] == hp_value].reset_index(drop=True) for df in dfs
    ]
    headers = ["Temp (C)", "Vdda (V)", "hp<1:0>"] + project_titles + ["Maximum"]

    for idx in range(len(filtered_dataframes[0])):
        temp_vdda_row = [
            filtered_dataframes[0].loc[idx, "Temp"],
            filtered_dataframes[0].loc[idx, "Vdda"],
            hp_value,
        ]

        project_data_row = [
            df.loc[idx, ivdda] if idx < len(df) else None for df in filtered_dataframes
        ]
        compliance_row = [
            filtered_dataframes[0].loc[idx, "Maximum"],
        ]

        row = temp_vdda_row + project_data_row + compliance_row
        row = [
            pd.to_numeric(val, errors="coerce") if isinstance(val, str) else val
            for val in row
        ]

        rows.append(row)

    rows_converted = [
        [
            (
                int(item)
                if isinstance(item, np.integer)
                else float(item) if isinstance(item, np.floating) else item
            )
            for item in row
        ]
        for row in rows
    ]

    converted_dataframes = pd.DataFrame(rows_converted)
    converted_dataframes.columns = headers
    _create_line_chart(converted_dataframes, hp_value, ivdda)


def _create_line_chart(dataframe, hp_value, table_name):
    df = pd.DataFrame(dataframe)

    # Melt the DataFrame to long format for seaborn
    df_melted = df.melt(id_vars=['Temp (C)', 'Vdda (V)', 'hp<1:0>'], var_name='Sample', value_name='Value')

    sns.set(style="whitegrid", context="talk")

    # Create the seaborn line plot
    plt.figure(figsize=(12, 8))
    sns.lineplot(data=df_melted, x='Temp (C)', y='Value', hue='Sample', style='Sample', markers=True, linewidth=2.5)
    
    # Add titles and labels
    plt.title(f"{table_name}",fontsize=16)
    plt.xlabel('Temp (C) & Vdda (V)',fontsize=14)
    plt.ylabel(f'{table_name}_{hp_value}',fontsize=14)
    plt.legend(title='Sample', title_fontsize='13', fontsize='11', bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

    # Show the plot
    plt.savefig(f'scripts/images/Chart_{table_name}_{hp_value}.jpg', bbox_inches='tight')
    print(f"\nSaved Image Ivdda_images/Chart_{table_name}_{hp_value}.jpg to the local directory")


gen_report()