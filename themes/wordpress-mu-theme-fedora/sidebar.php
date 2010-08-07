<!-- begin sidebar -->
<div id="sidebar">
 <div id="nav">
<ul id="wp-sidebar-list">
<?php 	/* Widgetized sidebar, if you have the plugin installed. */
		if ( !function_exists('dynamic_sidebar') || !dynamic_sidebar() ) : ?>
	<?php wp_list_pages('title_li=' . __('<h2>Pages:</h2>')); ?>
	<?php wp_list_bookmarks('title_after=</h2>&title_before=<h2>'); ?>
	<?php wp_list_categories('title_li=' . __('<h2>Categories:</h2>')); ?>
</ul>
   <h2><label for="s"><?php _e('Search:'); ?></label></h2>
   <form id="searchform" method="get" action="<?php bloginfo('home'); ?>">
	<div>
		<input type="text" name="s" id="s" size="15" /><br />
		<input type="submit" value="<?php _e('Search'); ?>" />
	</div>
	</form>
<h2><?php _e('Archives:'); ?></h2>
	<ul>
	 <?php wp_get_archives('type=monthly'); ?>
	</ul>
<h2><?php _e('Meta:'); ?></h2>
	<ul>
                <li><a href="https://blogs.fedoraproject.org/wp/wp-signup.php">Create a Blog</a></li>
		<?php if (is_user_logged_in()) { ?> <li><a href="/wp/wp-admin/">Control Panel</a></li><?php } ?>

		<li><?php wp_loginout(); ?></li>
		<li><a href="<?php bloginfo('rss2_url'); ?>" title="<?php _e('Syndicate this site using RSS'); ?>"><?php _e('<abbr title="Really Simple Syndication">RSS</abbr>'); ?></a></li>
		<li><a href="<?php bloginfo('comments_rss2_url'); ?>" title="<?php _e('The latest comments to all posts in RSS'); ?>"><?php _e('Comments <abbr title="Really Simple Syndication">RSS</abbr>'); ?></a></li>
		<li><a href="http://validator.w3.org/check/referer" title="<?php _e('This page validates as XHTML 1.0 Transitional'); ?>"><?php _e('Valid <abbr title="eXtensible HyperText Markup Language">XHTML</abbr>'); ?></a></li>
	</ul>
<h2><?php _e('Fedora Links:'); ?></h2>
	<ul>

		<li><a href="http://fedoraproject.org/">Fedora Project</a></li>
		<li><a href="http://planet.fedoraproject.org/">Planet Fedora</a></li>
		<li><a href="http://join.fedoraproject.org/">Join Fedora</a></li>
		<li><a href="http://fedoraproject.org/get-fedora">Get Fedora</a></li>
		<?php wp_meta(); ?>
	</ul>
<?php endif; ?>


 </div>
</div>
<!-- end sidebar -->
