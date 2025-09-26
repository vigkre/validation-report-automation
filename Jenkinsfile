pipeline {
/* -- Set the agent on which the build should execute -- */
    agent any
    stages {
        stage('Checkout Code'){
            steps{
                 git 'https://github.com/vigkre/validation-report-automation'   
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

