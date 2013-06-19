<?php
require_once('AuthPlugin.php');
class Auth_FAS extends AuthPlugin {

    var $fas_username;

    function setFasUsername($user) {
        $this->fas_username = $user;
    }

    function getFasUsername() {
        return $this->fas_username;
    }

    function authenticate(&$username, $password) {
        
        if ( ucfirst(strtolower($username)) != ucfirst($username) ) {
            return false;
        }

        $username = strtolower($username);
        $ch = curl_init();

        curl_setopt($ch, CURLOPT_URL, 'https://admin.fedoraproject.org/accounts/home');
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_USERAGENT, "Mediawiki FAS Auth 0.9.2");
        curl_setopt($ch, CURLOPT_POSTFIELDS, "user_name=".urlencode($username)."&password=".urlencode($password)."&login=Login");
        curl_setopt($ch, CURLOPT_HTTPHEADER, array('Accept: application/json'));
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);

        # WARNING: Never enable this line when running in production, as it will
        # cause plaintext passwords to show up in error logs.
        #curl_setopt($ch, CURLOPT_VERBOSE, TRUE);

        # The following two lines need to be uncommented when using a test FAS
        # with an invalid cert.  Otherwise they should be commented out (or set
        # to TRUE) for security.
        #curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, FALSE);
        #curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, FALSE);

        $response = json_decode(curl_exec($ch), true);
        curl_close ($ch);

        if (!isset($response['person']['id'])) {
            error_log("FAS auth failed for $username: incorrect username or password", 0);
            return false;
        }

        $groups = $response['memberships'];
        // let's make sure the username is consistent
        $this->setFasUsername(ucfirst(strtolower($response['person']['username'])));
        $username = $this->getFasUsername();

        for ($i = 0, $cnt = count($groups); $i < $cnt; $i++) {
            if ($groups[$i]["name"] == 'cla_done' && $response['person']['status'] == 'active') {
                error_log("FAS auth succeeded for $username", 0);
                return true;
            }
        }
        error_log("FAS auth failed for $username: insufficient group membership", 0);
        return false;
    }

    function userExists( $username ) {
        error_log("FAS [userExists]: $username, " . $this->getFasUsername(), 0);

        if (ucfirst(strtolower($username)) != $this->getFasUsername()) {
            error_log("FAS [userExists]: returned false", 0);
            return false;
        }                         
        error_log("FAS [userExists]: returned true", 0);
        return true;
    }

    function modifyUITemplate(&$template) {
        error_log("FAS [modifyUITemplate]: " . $this->getFasUsername(), 0);
        $template->set('create', false);
        $template->set('useemail', false);
        $template->set('usedomain', false);
    }

    function updateUser( &$user ){
        //error_log("FAS [updateUser]: " . $user->getName() . ", " . $this->getFasUsername(), 0);
        $user->setName($this->getFasUsername());
        $user->mEmail = strtolower($user->getName())."@fedoraproject.org";
        //error_log("FAS [updateUser]: " . $user->getName() . ", " . $this->getFasUsername(), 0);
        return true;
    }

    function autoCreate() {
        //error_log("FAS [autoCreate]: ", 0);
        return true;
    }

    function setPassword($password) {
        //error_log("FAS [setPassword]: $password", 0);
        return false;
    }

    function setDomain( $domain ) {
        //error_log("FAS [setDomain]: $domain", 0);
        $this->domain = $domain;
    }

    function validDomain( $domain ) {
        //error_log("FAS [validDomain]: $domain", 0);
        return true;
    }

    function updateExternalDB($user) {
        //error_log("FAS [updateExternalDB]: $user", 0);
        return true;
    }

    function canCreateAccounts() {
        //error_log("FAS [canCreateAccounts]:", 0);
        return false;
    }

    function addUser($user, $password) {
        //error_log("FAS [addUser]: $user, $password", 0);
        return true;
    }

    function strict() {
        //error_log("FAS [strict]:", 0);
        return true;
    }

    function strictUserAuth( $username ) {
        //error_log("FAS [strictUserAuth]: $username", 0);
        return true;
    }

    function allowPasswordChange() {
        //error_log("FAS [allowPasswordChange]:" . $this->getFasUsername(), 0);
        return false;
    }

    function getCanonicalName( $username ) {
        //error_log("FAS [getCanonicalName]: " . $username, 0);

        $username = str_replace('@fedoraproject.org', '', $username);

        //error_log("FAS [getCanonicalName]: returning... " . $username, 0);
        return $username;
    }

    function getUserInstance( &$user ) {
        //error_log("FAS [getUserInstance]: " . print_r($user), 0);
        return new AuthPluginUser( $user );
    }

    function initUser(&$user) {
        //error_log("FAS [initUser]: " . $user->getName() . ", " . $this->getFasUsername(), 0);
        $user->setName($this->getFasUsername());
        $user->mEmail = strtolower($user->getName())."@fedoraproject.org";
        $user->mEmailAuthenticated = wfTimestampNow();
        $user->setToken();
        $user->saveSettings();
        //error_log("FAS [initUser]: " . $user->getName() . ", " . $this->getFasUsername(), 0);
        return true;
    }
}

/**
 * Some extension information init
 */
$wgExtensionCredits['other'][] = array(
    'name' => 'Auth_FAS',
    'version' => '0.9.2',
    'author' => 'Nigel Jones',
    'description' => 'Authorisation plugin allowing login with FAS2 accounts'
);

?>
