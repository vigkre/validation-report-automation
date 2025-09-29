# Installing and Running MySQL with Sample Database

Download and install MySQL using MySQL installer from `https://dev.mysql.com/downloads/installer/`

Follow the steps in `https://www.mysqltutorial.org/getting-started-with-mysql/install-mysql/`

## Step 1: Navigate to MySQL Bin Directory

Open Command Prompt and navigate to the MySQL binary directory:

C:\Program Files\MySQL\MySQL Server 8.0\bin>

## Step 2: Launch MySQL Shel

.\mysql.exe -u root -p

You'll be prompted to enter your MySQL root password.

## Step 3: Load the Sample Database

source C:\Users\mysqlsampledatabase.sql

This will execute the SQL file and populate your MySQL server with the sample database.

## Step 4: Verify Database Installation

### Run the following command to list the databases

show databases;

## You should see output similar to

+--------------------+
| Database           |
+--------------------+
| classicmodels      |
| information_schema |
| mysql              |
| performance_schema |
| sys                |
+--------------------+
5 rows in set (0.00 sec)

The presence of the classicmodels database confirms the sample database was successfully imported.