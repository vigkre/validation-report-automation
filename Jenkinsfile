pipeline {
/* -- Set the agent on which the build should execute -- */
    agent any
    stages {
        stage('Run LabVIEW VI') {
            script {
                def labviewCommand = 'LabVIEWCLI -OperationName RunVI -VIPath "scripts\\Ivdda_insert_db.vi" "scripts\\trial 15_Ivdda1v5.csv" Ivdda0v9_tx_master S08SSSW'
                bat labviewCommand
            }
        }
        stage('Run Python Script') {
            script {
                def pythonCommand = 'python scripts\\generate_chart.py'
                bat pythonCommand
            }
        }
    }
}
