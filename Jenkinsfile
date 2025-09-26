pipeline {
/* -- Set the agent on which the build should execute -- */
    agent any
    stages {
        stage("Checkout Code") {
            steps {
                 git "https://github.com/vigkre/validation-report-automation"
            }            
        }
        stage('Run Python Script') {
            steps {
                script {
                    def pythonCommand = "python scripts\\test_script.py"
                    bat pythonCommand
                }
            }
        }
    }
}






