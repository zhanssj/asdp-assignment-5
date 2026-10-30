import jenkins.model.Jenkins
import hudson.model.*
import hudson.security.*
import hudson.slaves.*
import jenkins.slaves.JnlpAgentReceiver
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition
import hudson.plugins.git.GitSCM
import hudson.plugins.git.BranchSpec
import hudson.plugins.git.UserRemoteConfig

def j = Jenkins.get()
j.setNumExecutors(0)
j.setSystemMessage('ASDP Assignment 5 | Smart City Sensor Data Analyzer | local research CI/CD')
def realm = new HudsonPrivateSecurityRealm(false)
if (User.getById('admin', false) == null) {
    realm.createAccount('admin', new File('/run/secrets/admin_password').text.trim())
}
j.setSecurityRealm(realm)
def authorization = new FullControlOnceLoggedInAuthorizationStrategy()
authorization.setAllowAnonymousRead(false)
j.setAuthorizationStrategy(authorization)
j.setCrumbIssuer(new hudson.security.csrf.DefaultCrumbIssuer(true))
jenkins.model.JenkinsLocationConfiguration.get().setUrl('http://localhost:8081/')

if (j.getNode('docker-agent') == null) {
    j.addNode(new DumbSlave('docker-agent', 'Local container build agent', '/home/jenkins/agent',
        '1', Node.Mode.NORMAL, 'docker-python', new JNLPLauncher(true),
        new RetentionStrategy.Always(), new ArrayList()))
}
new File('/run/agent-auth/secret').text = JnlpAgentReceiver.DATABASE.getSecretOf('docker-agent')

def url = System.getenv('SCM_URL') ?: 'https://github.com/zhanssj/asdp-assignment-5.git'
if (url.startsWith('file:')) {
    // Optional offline classroom mode; source is explicitly mounted read-only.
    System.setProperty('hudson.plugins.git.GitSCM.ALLOW_LOCAL_CHECKOUT', 'true')
}
def scm = new GitSCM([new UserRemoteConfig(url, null, null, null)],
    [new BranchSpec('*/main')], false, [], null, null, [])
def job = j.getItem('asdp-assignment-5') ?: j.createProject(WorkflowJob, 'asdp-assignment-5')
def definition = new CpsScmFlowDefinition(scm, 'infra/Jenkinsfile')
definition.setLightweight(true)
job.setDefinition(definition)
job.setDescription('Tests, Docker image build, HTTP verification and local deployment. Pipeline: infra/Jenkinsfile.')
job.save()
j.save()
println('Assignment 5 controller and build agent configured.')
