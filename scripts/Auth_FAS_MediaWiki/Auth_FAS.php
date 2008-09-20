<?php
	require_once('AuthPlugin.php');
	class Auth_FAS extends AuthPlugin {
		function authenticate($username, $password) {
                        if ( ucfirst(strtolower($username)) != ucfirst($username) ) {
                                return false;
                        }

			$username = strtolower( $username);
			$ch = curl_init();

			curl_setopt($ch, CURLOPT_URL, 'https://admin.fedoraproject.org/accounts/json/person_by_username?tg_format=json');
			curl_setopt($ch, CURLOPT_POST, 1);
			curl_setopt($ch, CURLOPT_USERAGENT, "Auth_FAS 0.9");
			curl_setopt($ch, CURLOPT_POSTFIELDS, "username=".urlencode($username)."&user_name=".urlencode($username)."&password=".urlencode($password)."&login=Login");
			curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
			curl_setopt($ch, CURLOPT_VERBOSE, 1);
			# I hate chained certificates
			curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, FALSE);
			# This is only required because of the wildcard cert on pt10
			curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, FALSE);
			$response = json_decode(curl_exec($ch), true);
			curl_close ($ch);

			if (!isset($response["success"])) return false;

			$groups = $response["person"]["approved_memberships"];

			for ($i = 0, $cnt = count($groups); $i < $cnt; $i++) {
   				if ($groups[$i]["name"] = "cla_done") {
				       return true;
				}
			}
			return false;
		}

		function userExists( $username ) {
			if ( ucfirst(strtolower($username)) != ucfirst($username) ) {
				return false;
			}
			return true;
		}

		function modifyUITemplate(&$template) {
			$template->set('create',	false);
			$template->set('useemail',	false);
			$template->set('usedomain',	false);
		}
		
		function updateUser( &$user ){
			$user->mEmail	=	strtolower($user->getName())."@fedoraproject.org";
			return true;
		}

		function autoCreate() {
			return true;
		}

		function setPassword($password) {
			return false;
		}

		function setDomain( $domain ) {
			$this->domain = $domain;
		}

		function validDomain( $domain ) {
			return true;
		}

		function updateExternalDB($user) {
			return true;
		}

		function canCreateAccounts() {
			return false;
		}

		function addUser($user, $password) {
			return true;
		}

		function strict() {
			return true;
		}

		function strictUserAuth( $username ) {
			return true;
		}

		function allowPasswordChange() {
			return false;
		}

		function initUser(&$user) {
			$user->mEmail	=	strtolower($user->getName())."@fedoraproject.org";
			$user->mEmailAuthenticated =	wfTimestampNow();
			$user->setToken();
			$user->saveSettings();
			return true;
		}
	}

/**
 * Some extension information init
 */
$wgExtensionCredits['other'][] = array(
   'name' => 'Auth_FAS',
   'version' => '0.9',
   'author' => 'Nigel Jones',
   'description' => 'Authorisation plugin allowing login with FAS2 accounts'#,
#   'url' => 'http://www.mediawiki.org/wiki/Extension:PwAuthPlugin'
);

?>
