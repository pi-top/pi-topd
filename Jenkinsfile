@Library('devops-jenkins-shared-library@master') _

pipeline {
  agent { label 'master' }
  options {
    timestamps()
    ansiColor('xterm')
  }
  stages {
    stage ('Checkout Repository') {
      steps {
        checkoutSubmodule()
      }
    }

    stage ('Pre-commit Checks') {
      steps {
        script {
          REPO_NAME = env.JOB_NAME.split('/')[1]
          PKG_NAME  = REPO_NAME.substring(0, REPO_NAME.length() - 4)
        }
        dir(PKG_NAME) {
          preCommit()
        }
      }
    }

    stage ('Build') {
      steps {
        buildGenericPkg()
      }
    }

    stage ('Test') {
      steps {
        runPythonUnitTesting(env.WORKSPACE + "/pt-device-manager/private-Device-Management/tests/", env.WORKSPACE + "/pt-device-manager/private-Device-Management/pt-device-manager/") 

        checkSymLinks()
        shellcheck()
        script {
          try {
            lintian()
          } catch (e) {
            currentBuild.result = 'UNSTABLE'
          }
        }
      }
    }

    stage ('Publish') {
      steps {
        publishSirius()
      }
    }
  }
  post {
    failure {
      slackSend color: "danger",
      message: "Job: <${JOB_URL}|${env.JOB_NAME}> build <${env.BUILD_URL}|${env.BUILD_NUMBER}> failed or rejected",
      channel: "#os-devs"
    }
  }
}
