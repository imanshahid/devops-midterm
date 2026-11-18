pipeline {
  agent any
  options { timestamps(); disableConcurrentBuilds(); timeout(time: 15, unit: 'MINUTES') }
  triggers { githubPush() }
  environment {
    STUDENT_ID = 'SP23-BAI-018'          // matches student_id in config.json
    IMAGE      = 'midterm-app'
    CONTAINER  = 'midterm-app'
    NOTIFY_TO  = 'qasimalik@gmail.com'          // instructor
    SELF_TO    = 'imanshahid142003@gmail.com'   // test mails go here
  }
  stages {
    stage('Checkout latest') {
      steps {
        checkout scm
        script { env.SHORT_SHA = env.GIT_COMMIT.take(7) }
      }
    }
    stage('Train') {
      steps {
        sh '''
          docker build --target base -t ${IMAGE}-ci .
          docker run --rm --user $(id -u):$(id -g) -e GIT_COMMIT=${GIT_COMMIT} \
            -v "$PWD":/app -w /app ${IMAGE}-ci python train.py
        '''
      }
    }
    stage('Test') {
      steps {
        sh '''
          docker run --rm --user $(id -u):$(id -g) \
            -v "$PWD":/app -w /app ${IMAGE}-ci python -m pytest -q tests
        '''
      }
    }
    stage('Build image') {
      steps {
        sh 'docker build --target final -t ${IMAGE}:${SHORT_SHA} -t ${IMAGE}:latest .'
      }
    }
    stage('Deploy on EC2') {
      steps {
        sh '''
          docker rm -f ${CONTAINER} || true
          docker run -d --name ${CONTAINER} --restart unless-stopped -p 8000:8000 ${IMAGE}:${SHORT_SHA}
          for i in $(seq 1 20); do
            curl -fs localhost:8000/metrics | grep -q "${GIT_COMMIT}" && exit 0
            sleep 3
          done
          echo "Deployed app did not report the new commit"; exit 1
        '''
      }
    }
    stage('Push to Docker Hub') {
      steps {
        catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
          withCredentials([usernamePassword(credentialsId: 'dockerhub',
                           usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
            sh '''
              echo "$DH_PASS" | docker login -u "$DH_USER" --password-stdin
              docker tag ${IMAGE}:latest $DH_USER/${IMAGE}:latest
              docker tag ${IMAGE}:latest $DH_USER/${IMAGE}:${SHORT_SHA}
              docker push $DH_USER/${IMAGE}:latest
              docker push $DH_USER/${IMAGE}:${SHORT_SHA}
              docker image prune -f
            '''
          }
        }
      }
    }
  }
  post {
    always {
      script {
        env.METRICS = sh(returnStdout: true, script: 'cat artifacts/metrics.json || echo "metrics unavailable"').trim()
        // Instructor is emailed on every build EXCEPT manual "Build Now" clicks
        // and commits whose message contains [skip-mail]. Those go to me only.
        def causes  = currentBuild.getBuildCauses().toString()
        def lastMsg = sh(returnStdout: true, script: 'git log -1 --pretty=%B || true').trim()
        def testRun = causes.contains('UserIdCause') || lastMsg.contains('[skip-mail]')
        env.MAIL_TO  = testRun ? env.SELF_TO : env.NOTIFY_TO
        env.MAIL_TAG = testRun ? '[TEST] ' : ''
      }
      emailext(
        to: "${env.MAIL_TO}",
        subject: "${env.MAIL_TAG}[${env.STUDENT_ID}] MIDTERM-${env.STUDENT_ID} build #${env.BUILD_NUMBER}: ${currentBuild.currentResult}",
        mimeType: 'text/plain',
        body: """Student Reg No: ${env.STUDENT_ID}
Result: ${currentBuild.currentResult}
Commit: ${env.GIT_COMMIT}
Build URL: ${env.BUILD_URL}

Metrics:
${env.METRICS}
"""
      )
    }
  }
}
