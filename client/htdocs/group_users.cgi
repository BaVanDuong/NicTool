#!/usr/bin/perl
#
# NicTool v2.00-rc1 Copyright 2001 Damon Edwards, Abe Shelton & Greg Schueler
# NicTool v2.01 Copyright 2004 The Network People, Inc.
#
# NicTool is free software; you can redistribute it and/or modify it under
# the terms of the Affero General Public License as published by Affero,
# Inc.; either version 1 of the License, or any later version.
#
# NicTool is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE. See the Affero GPL for details.
#
# You should have received a copy of the Affero General Public License
# along with this program; if not, write to Affero Inc., 521 Third St,
# Suite 225, San Francisco, CA 94107, USA
#

use strict;

require 'nictoolclient.conf';

main();

sub main {
    my $q      = new CGI();
    my $nt_obj = new NicToolClient($q);

    return if $nt_obj->check_setup ne 'OK';

    my $user = $nt_obj->verify_session();

    if ($user) {
        print $q->header;
        display( $nt_obj, $q, $user );
    }
}

sub display {
    my ( $nt_obj, $q, $user ) = @_;

    $nt_obj->parse_template($NicToolClient::start_html_template);
    $nt_obj->parse_template(
        $NicToolClient::body_frame_start_template,
        username  => $user->{'username'},
        groupname => $user->{'groupname'},
        userid    => $user->{'nt_user_id'}
    );

    my $level = $nt_obj->display_group_tree(
        $user,
        $user->{'nt_group_id'},
        $q->param('nt_group_id'), 0
    );

    $nt_obj->display_user_list_options( $user, $q->param('nt_group_id'),
        $level, 1 );
    my $group = $nt_obj->get_group( nt_group_id => $q->param('nt_group_id') );

    my @fields = qw/ user_create user_delete user_write group_create group_delete group_write zone_create zone_delegate zone_delete zone_write zonerecord_create zonerecord_delegate zonerecord_delete zonerecord_write nameserver_create nameserver_delete nameserver_write self_write /;
    if ( $q->param('new') ) {
        if ( $q->param('Create') ) {
            my %data;
            foreach ( qw( nt_group_id username first_name last_name email password password2 ) )
            {
                $data{$_} = $q->param($_);
            }
            if ( $q->param('group_defaults') eq '0' ) {
                foreach (@fields) {
                    $data{$_} = $q->param($_) ? 1 : 0;
                }
            }
            else {
                $data{'inherit_group_permissions'} = 1;
            }

            #warn Data::Dumper::Dumper(\%data);
            my $error = $nt_obj->new_user(%data);

            if ( $error->{'error_code'} != 200 ) {
                display_edit_user( $nt_obj, $user, $group, $q, $error, 'new' );
            }
        }
        elsif ( $q->param('Cancel') ) {

            # do nothing
        }
        else {
            display_edit_user( $nt_obj, $user, $group, $q, '', 'new' );
        }
    }
    elsif ( $q->param('edit') ) {
        if ( $q->param('Save') ) {
            my %data;
            foreach (
                qw(nt_user_id nt_group_id username first_name last_name email password password2)
                )
            {
                $data{$_} = $q->param($_);
            }
            if ( $q->param('group_defaults') eq '0' ) {
                foreach (@fields) {
                    $data{$_} = $q->param($_) ? 1 : 0;
                }
            }
            else {
                $data{'inherit_group_permissions'} = 1;
            }
            my $error = $nt_obj->edit_user(%data);

            if ( $error->{'error_code'} != 200 ) {
                display_edit_user( $nt_obj, $user, $group, $q, $error,
                    'edit' );
            }
        }
        elsif ( $q->param('Cancel') ) {

            # do nothing
        }
        else {
            display_edit_user( $nt_obj, $user, $group, $q, '', 'edit' );
        }
    }

    if ( $q->param('delete') ) {
        my $error
            = $nt_obj->delete_users( user_list => $q->param('obj_list') );
        if ( $error->{'error_code'} != 200 ) {
            $nt_obj->display_nice_error( $error, "Delete Users" );
        }
    }

    display_list( $nt_obj, $q, $group, $user );

    $nt_obj->parse_template($NicToolClient::end_html_template);
}

sub display_edit_user {
    my ( $nt_obj, $user, $group, $q, $message, $edit ) = @_;

    my $showpermissions = 1;
    my $modifyperm
        = $user->{ 'user_' . ( $edit eq 'edit' ? 'write' : 'create' ) };
    if ($modifyperm) {
        print $q->start_form(
            -action => 'group_users.cgi',
            -method => 'POST',
            -name   => 'perms_form'
        );
        print $q->hidden( -name => $edit );
        print $q->hidden( -name => 'nt_group_id' );
        print $q->hidden( -name => 'nt_user_id' ) if $edit eq 'edit';
    }

    $nt_obj->display_nice_error($message) if $message;

    print qq[<table class="fat">
<tr class=dark_bg><td colspan=2><b>New User</b></td></tr>
<tr class=light_grey_bg>
<td class=right>Username:</td>
<td class=width80>],
        (
        $modifyperm
        ? $q->textfield(
            -name      => 'username',
            -size      => 40,
            -maxlength => 50
            )
        : ''
        ),
        qq[</td></tr>
<tr class=light_grey_bg>
<td class=right>First Name:</td>
<td class=width80>],
( $modifyperm ? $q->textfield( -name => 'first_name', -size => 20, -maxlength => 30) : ''),
        qq[</td></tr>
<tr class=light_grey_bg>
<td class=right>Last Name:</td>
<td class=width80>],
( $modifyperm ? $q->textfield( -name => 'last_name', -size => 30, -maxlength => 40) : ''),
        qq[</td></tr>
<tr class=light_grey_bg>
<td class=right>Email Address:</td>
<td class=width80>],
( $modifyperm ? $q->textfield( -name => 'email', -size => 40, -maxlength => 100 ) : ''),
        qq[</td></tr>
    <tr class=light_grey_bg>
    <td class=right>Password:</td>
    <td class=width80>],
( $modifyperm ? $q->password_field( -name => 'password', -size => 15, -maxlength => 15) : ''),
        qq[</td></tr>
<tr class=light_grey_bg>
<td class=right>Password (Again):</td>
<td style="width:80%;">],
( $modifyperm ? $q->password_field( -name => 'password2', -size => 15, -maxlength => 15) : ''),
        qq[</td></tr>];

    if ($showpermissions) {
        my %perms = (
            group      => [qw(write create delete .)],
            user       => [qw(write create delete .)],
            zone       => [qw(write create delete delegate)],
            zonerecord => [qw(write create delete delegate)],
            nameserver => [qw(write create delete . )],
            self       => [qw(write . . . )]
        );
        my %labels = (
            group      => { 'write' => 'Edit' },
            user       => { 'write' => 'Edit' },
            zone       => { 'write' => 'Edit' },
            zonerecord => { 'write' => 'Edit' },
            nameserver => { 'write' => 'Edit' },
            self       => { 'write' => 'Edit' },
        );
        my @order = qw(group user zone zonerecord nameserver self);

        print qq[
<tr class=dark_grey_bg><td colspan=2>
 <input type=radio value='1' name='group_defaults' CHECKED>This user inherits the permissions defined for the enclosing group ] . $nt_obj->help_link('perms') . qq[
 </td></tr>
<tr class=light_grey_bg>
 <td colspan=2 class=light_grey_bg>
  <table class="center" style="padding:6; border-spacing:1;"> ];
        my $x = 1;
        my $color;
        foreach my $type (@order) {
            $color = ( $x++ % 2 == 0 ? 'light_grey_bg' : 'white_bg' );
            print qq{<tr><td class="right bold">} . ucfirst($type) . qq{:</td>};
            foreach my $perm ( @{ $perms{$type} } ) {
                if ( $perm eq '.' ) {
                    print qq[ <td class=$color></td>];
                    next;
                }
                my $check = $group->{ $type . "_" . $perm } ? 'checked.gif' : 'unchecked.gif';
                print qq[
                    <td class="$color left middle"><img src="$NicToolClient::image_dir/perm-$check"> ]
                    . ( exists $labels{$type}{$perm} ? $labels{$type}{$perm} : ucfirst($perm) )
                    . qq{</td>};
            }
            print qq[</tr>];
        }
        print qq[ </table> </td> </tr>
<tr class=dark_grey_bg><td colspan=2>
 <input type=radio value='0' name='group_defaults'>This user uses the permissions defined below ],
            $nt_obj->help_link('perms'),
            qq[</td></tr>
<tr class=light_grey_bg>
 <td colspan=2 class=light_grey_bg>
  <table class="center" style="padding:6; border-spacing:1;">
];
    $x     = 1;
    @order = qw/ group user zone zonerecord nameserver self header /;
    foreach my $type (@order) {

            if ( $type eq 'header' ) {
                print qq(
                    <tr><td></td>
                );
                foreach (qw(Edit Create Delete Delegate All)) {
                    if ( $_ eq '.' ) {
                        print "<td></td>";
                        next;
                    }
                    print "<td>";
                    print $q->checkbox(
                        -name  => "select_all_$_",
                        -label => '',
                        -onClick =>
                            "selectAll$_(document.perms_form, this.checked);",
                        -override => 1
                    );
                    print "</td>";
                }
                print qq(
                    </tr>
                );
            }
            else {
                $color = (
                    $x++ % 2 == 0 ? 'light_grey_bg' : 'white_bg' );
                print qq{
                        <tr>
                            <td class=right><b>}
                    . ( ucfirst($type) ) . qq{:</b></td>
                                };
                foreach my $perm ( @{ $perms{$type} } ) {
                    if ( $perm eq '.' ) {
                        print qq(
                            <td>&nbsp;</td>
                        );
                        next;
                    }
                    if ( $user->{ $type . "_" . $perm } ) {
                        print qq{<td class="$color left middle"> };
                        print $q->checkbox(
                            -name    => $type . "_" . $perm,
                            -value   => '1',
                            -checked => $group->{ $type . "_" . $perm },
                            -label   => ''
                            )
                            . (
                            exists $labels{$type}->{$perm}
                            ? $labels{$type}->{$perm}
                            : ucfirst($perm) )
                            . qq{</td> };
                    }
                    else {
                        print qq{<td class="$color middle left"><img src="$NicToolClient::image_dir/perm-}
                            . ( $group->{ $type . "_" . $perm } ? 'checked.gif' : 'unchecked.gif' )
                            . qq{" alt=""><span class=disabled>}
                            . ( exists $labels{$type}->{$perm} ? $labels{$type}->{$perm} : ucfirst($perm) )
                            . qq{</span></td> };
                    }
                }
                print "<td>",
                     $q->checkbox(
                    -name    => "select_all_$type",
                    -label   => '',
                    -onClick => "selectAll"
                        . ucfirst($type)
                        . "(document.perms_form, this.checked);",
                    -override => 1
                    ), 
                    "</td> </tr>";
            }
        }
        print qq{
                </table>
            </td>
        </tr>
        };
    }
    if ($modifyperm) {
        print qq[<tr class=dark_grey_bg><td colspan=2 class=center>],
            $q->submit( $edit eq 'edit' ? 'Save' : 'Create' ),
            $q->submit('Cancel'), "</td></tr>";
    }
    print "</table>";
    print $q->end_form;
}

sub display_list {
    my ( $nt_obj, $q, $group, $user ) = @_;

    my $cgi = 'group_users.cgi';

    my $user_group = $nt_obj->get_group( nt_group_id => $user->{'nt_group_id'} );

    my @columns = qw(username first_name last_name email);

    my %labels = (
        username   => 'User',
        first_name => 'First Name',
        last_name  => 'Last Name',
        email      => 'Email',
        group_name => 'Group'
    );

    my $include_subgroups = $group->{'has_children'} ? 'sub-groups' : undef;
    if ($include_subgroups) {
        unshift( @columns, 'group_name' );
    }

    my %params = ( nt_group_id => $q->param('nt_group_id') );
    my %sort_fields;
    $nt_obj->prepare_search_params( $q, \%labels, \%params, \%sort_fields,
        100 );

    $sort_fields{'username'} = { 'order' => 1, 'mod' => 'Ascending' }
        unless %sort_fields;

    my $rv = $nt_obj->get_group_users(%params);

    $nt_obj->display_sort_options( $q, \@columns, \%labels, $cgi,
        ['nt_group_id'], $include_subgroups )
        if $q->param('edit_sortorder');
    $nt_obj->display_advanced_search( $q, \@columns, \%labels, $cgi,
        ['nt_group_id'], $include_subgroups )
        if $q->param('edit_search');

    return $nt_obj->display_nice_error( $rv, "Get Group Users" )
        if ( $rv->{'error_code'} != 200 );

    my $list = $rv->{'list'};
    my $map  = $rv->{'group_map'};

    my @state_fields;
    foreach ( @{ $nt_obj->paging_fields } ) {
        push( @state_fields, "$_=" . $q->escape( $q->param($_) ) )
            if $q->param($_);
    }
    my $gid = $q->param('nt_group_id');
    my $state_string = @state_fields ? join('&amp;', @state_fields) : 'not_empty=1';

    print qq[
<table class="fat">
 <tr class=dark_grey_bg><td>
   <table class="no_pad fat">
    <tr>
     <td class="bold">User List</td>
     <td class="right">];
    if ( $user->{'user_create'} ) {
        print qq[<a href="$cgi?$state_string&amp;nt_group_id=$gid&amp;new=1">New User</a>];
    }
    else {
        print "<span class=disabled>New User</span>";
    }
    print qq[ | <a href="javascript:void open_move(document.list_form.obj_list);">Move Selected Users</a>]
        if ( @$list && $user_group->{'has_children'} );
    print qq[
     </td>
    </tr>
   </table>
  </td>
 </tr>
</table>];

    $nt_obj->display_search_rows( $q, $rv, \%params, $cgi, ['nt_group_id'],
        $include_subgroups );

    if ( ! @$list) {
        print $q->endform;
        return;
    };

    $nt_obj->display_move_javascript( 'move_users.cgi', 'user' );

    print qq[<table class="fat"> <tr class=dark_grey_bg>];

    if ( $user_group->{'has_children'} ) {
        print qq[<td class=center>
        <table class="no_pad">
        <tr><td></td>],
        "\n",
        $q->startform(
            -action => 'move_users.cgi',
            -method => 'POST',
            -name   => 'list_form',
            -target => 'move_win'
        ), "\n",
        "<td></td></tr></table>";

        print (
            $rv->{'total'} == 1 ? '&nbsp;' : $q->checkbox(
                -name  => 'select_all_or_none',
                -label => '',
                -onClick => 'selectAllorNone(document.list_form.obj_list, this.checked)',
                -override => 1
            )
        ),
        "</td>";
    }

    foreach (@columns) {
        if ( $sort_fields{$_} ) {
            my $dir = uc( $sort_fields{$_}->{'mod'} ) eq 'ASCENDING' ? 'up' : 'down';
            print qq[<td class="dark_bg center">
 <table class="no_pad">
  <tr>
   <td>$labels{$_}</td>
   <td>&nbsp; &nbsp; $sort_fields{$_}->{'order'}</td>
   <td><img src=$NicToolClient::image_dir/$dir.gif></td>
  </tr></table></td>];
        }
        else {
            print "<td class=center>$labels{$_}</td>";
        }
    }
    print qq[<td class="width1"><img src="$NicToolClient::image_dir/trash.gif"></td></tr>];

    my $x     = 0;
    my $width = int( 100 / @columns ) . '%';

    foreach my $obj (@$list) {
        my $bgcolor = $x++ % 2 == 0 ? 'light_grey_bg' : 'white_bg';
        print "<tr class=$bgcolor>";
        if (   $user->{'user_write'}
            && $obj->{'nt_user_id'} ne $user->{'nt_user_id'} )
        {
            if ( $user_group->{'has_children'} ) {
                print qq[<td class="width1 center">],
                    $q->checkbox( -name => 'obj_list', -value => $obj->{'nt_user_id'}, 
                        -label => ''), '</td>';
            };
        }
        else {
            if ( $user_group->{'has_children'} ) {
                print qq[<td class="width1 center">
<img src="$NicToolClient::image_dir/nobox.gif" alt="nobox"></td>];
            };
        }

        if ($include_subgroups) {
            print qq[<td style="width:$width;"><table class="no_pad"><tr>
            <td><img src="$NicToolClient::image_dir/group.gif"></td>];
            if ($map) {
                print "<td>",
                    join(
                    ' / ',
                    map(qq[<a href="group.cgi?nt_group_id=$_->{'nt_group_id'}">$_->{'name'}</a>],
                        (   @{ $map->{ $obj->{'nt_group_id'} } },
                            {   nt_group_id => $obj->{'nt_group_id'},
                                name        => $obj->{'group_name'}
                            }
                            ) )
                    ),
                    "</td>";
            }
            else {
                print "<td>",
                    join(
                    ' / ',
                    map(qq[<a href="group.cgi?nt_group_id=$_->{'nt_group_id'}">$_->{'name'}</a>],
                        (   {   nt_group_id => $obj->{'nt_group_id'},
                                name        => $obj->{'group_name'}
                            }
                            ) )
                    ),
                    "</td>";
            }
            print "</tr></table></td>";
        }

        my $url = "user.cgi?nt_user_id=$obj->{'nt_user_id'}&amp;nt_group_id=$obj->{'nt_group_id'}";
        print qq[
<td style="width:$width;"><table class="no_pad">
  <tr>
   <td><a href="$url"><img src="$NicToolClient::image_dir/user.gif"></a></td>
   <td><a href="$url">$obj->{'username'}</a></td>
  </tr>
 </table>
</td>
<td style="width:$width;">$obj->{'first_name'}</td>
<td style="width:$width;">$obj->{'last_name'}</td>
<td style="width:$width;"><a href="mailto:$obj->{'email'}">$obj->{'email'}</a>
</td>];

        if (    $user->{'user_delete'}
            and $obj->{'nt_user_id'} != $user->{'nt_user_id'} )
        {
            my $gid = $q->param('nt_group_id');
            my $state_string = join('&amp;', @state_fields);
            print qq[<td class="width1">
 <a href="$cgi?$state_string&amp;nt_group_id=$gid&amp;delete=1&amp;obj_list=$obj->{'nt_user_id'}" onClick="return confirm('Delete user $obj->{'username'}?');"><img src="$NicToolClient::image_dir/trash.gif" alt="trash"></a></td>];
        }
        else {
            print qq[<td class="width1"><img src="$NicToolClient::image_dir/trash-disabled.gif" alt="disabled trash"></td>];
        }
        print qq[</tr>];
    }

    print qq[</table>];

    print $q->endform;
}
