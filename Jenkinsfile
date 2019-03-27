library 'devops-jenkins-shared-library@master'

pipeline {
  agent { label 'master'}
  options {
    timestamps()
    ansiColor('xterm')
  }
  stages {
    stage ('Checkout Repository') {
      checkoutSubmodule()
    }
    stage ('Build') {
      buildGenericPkg()
    }
    stage ('Test') {
      checkSymLinks()
      shellcheck()
      script{
        try {
          lintian()
        } catch (e) {
          currentBuild.result = 'UNSTABLE'
        }

      }
    }

    stage ('Publish') {
      publishSirius()
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
