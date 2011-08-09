# Copyright 2004-2011 Gentoo Foundation
# Distrubuted under the terms of the GNU General Public Licence v2

# Authors:
# koirky <kiorky@cryptelium.net> The code:
# ali_bush <ali_bush@gentoo.org> Refactored into module.
# Kasun Gajasinghe <kasunbg@gmail.com> improved pom rewrite feature
# Python based POM navigator

# Changelog
# Kasun Gajasinghe <kasunbg@gmail.com>
# 07/08/2011 Add pom's parent-element rewrite feature
#
# Kasun Gajasinghe <kasunbg@gmail.com>
# 11/07/2011 Improved pom rewriting feature - plugin rewrite
#
# ali_bush <ali_bush@gentoo.org>
# 31/12/07 Refacted by separating MavenPom into namespace
#
# kiorky <kiorky@cryptelium.net>
# 31/05/2007 Add rewrite feature
#
# kiorky <kiorky@cryptelium.net>
# 08/05/2007 initial version

import sys
import StringIO

# either a very simplified representation of a maven pom
# or a fully xml rewritten pom
class MavenPom:
    def __init__(self,cli_options = None):
        self.group  = ''
        self.artifact = ''
        self.version = ''
        self.name = ''
        self.is_child = "false"
        self.dependencies = []
        self.buffer = StringIO.StringIO()
        self.__write = self.buffer.write
        self.mydoc = None
        self.cli_options = cli_options

        
    def getInfos(self,node):
        for child_node in node.childNodes:
            if child_node.nodeType == child_node.ELEMENT_NODE:
                if child_node.childNodes:
                    if child_node.childNodes[0].nodeValue != "":
                        if child_node.nodeName == "version":
                            self.version = child_node.childNodes[0].nodeValue

                        if child_node.nodeName == "artifactId":
                            self.artifact = child_node.childNodes[0].nodeValue

                        if child_node.nodeName == "groupId":
                            self.group = child_node.childNodes[0].nodeValue

                        if child_node.nodeName == "name":
                            self.name = child_node.childNodes[0].nodeValue


    def getDescription(self,mydoc,**kwargs):
        if mydoc:
            self.project = mydoc.getElementsByTagName("project")[0]
            # get inherited properties from parent pom if any
            if self.group == "" or self.version == "" or self.artifact == "":
                for node in self.project.childNodes:
                    if node.nodeName == "parent":
                        self.is_child = "true"
                        self.getInfos(node)

            self.getInfos(self.project)

            # get our deps
            for node in self.project.childNodes:
                if node.nodeName == "dependencies":
                    for dependency_node in node.childNodes:
                        if dependency_node.nodeName == "dependency":
                            dep = MavenPom()
                            for child_node in dependency_node.childNodes:
                                if child_node.nodeType == child_node.ELEMENT_NODE:
                                    dep.getInfos(child_node)

                            self.dependencies.append(dep)

            if self.cli_options.p_group:
                self.__write("pom group:%s\n" % self.group )

            if self.cli_options.p_ischild:
                self.__write("pom ischild:%s\n" % self.is_child )

            if self.cli_options.p_artifact:
                self.__write("pom artifact:%s\n" % self.artifact )

            if self.cli_options.p_version:
                self.__write("pom version:%s\n" % self.version )

            if self.cli_options.p_dep:
                i=0
                for dependency in self.dependencies:
                    i=i+1
                    self.__write("%d:dep_group:%s\n" % (i,dependency.group) )
                    self.__write("%d:dep_artifact:%s\n" % (i,dependency.artifact) )
                    self.__write("%d:dep_version:%s\n" % (i,dependency.version) )

    def read(self):
        return self.buffer.getvalue()

    def parent_rewrite(self, xmldoc, **kwargs):
    #rewrite the <parent> element in the poms with the values in self.cli_options.{p_parentgroup,p_parentartifact,p_parentversion}
    #This rewriting is optional. Packager may only rewrite version of the parent element as well if he wishes.
    #This does not touch the parent pom.
        parent_elements = ( xmldoc.getElementsByTagName("parent") or [] )
        if parent_elements:
            parent_element = parent_elements[0]
            if self.cli_options.p_parentgroup:
                current_pgroup = parent_element.getElementsByTagName("groupId")[0]
                parent_element.removeChild( current_pgroup )
                current_pgroup.unlink()
                parent_element.appendChild( self.create_element(xmldoc, "groupId", self.cli_options.p_parentgroup[0] ) )
            if self.cli_options.p_parentartifact:
                current_partifact = parent_element.getElementsByTagName("artifactId")[0]
                parent_element.removeChild( current_partifact )
                current_partifact.unlink()
                parent_element.appendChild( self.create_element(xmldoc, "artifactId", self.cli_options.p_parentartifact[0] ) )
            if self.cli_options.p_parentversion:
                current_pversion = parent_element.getElementsByTagName("version")[0]
                parent_element.removeChild( current_pversion )
                current_pversion.unlink()
                parent_element.appendChild( self.create_element(xmldoc, "version", self.cli_options.p_parentversion[0] ) )
            #	else:
            #		create parent element and map the parent to gentoo maven super pom. That contains all the plugin versions etc.

    def rewrite(self, xmldoc, **kwargs):
        #rewrite the parent element of all poms if set 
        if self.cli_options.p_rewrite_parent:
	    	self.parent_rewrite(xmldoc)
            
	#append <parent> element to pom if it does not exist.
	#If set p_rewrite_parent set, a <parent> will be _created_ or rewritten according to the given input.
	#parent_rewrite takes precedence over this if set
	parent_elements = ( xmldoc.getElementsByTagName("parent") or [] )
	if not parent_elements:
		project_node = xmldoc.getElementsByTagName("project")[0]		
		parent_element =  self.create_element(xmldoc, "parent" )
		
		parent_element.appendChild( self.create_element(xmldoc, "groupId", "gentoo"))
		parent_element.appendChild( self.create_element(xmldoc, "artifactId", "gentoo-superpom"))

		#set superpom_version
		superpom_version=1
		#cmd argument
		if self.cli_options.p_superpom_version:
			superpom_version=self.cli_options.p_superpom_version
		parent_element.appendChild( self.create_element(xmldoc, "version", "%s" % superpom_version ))
		project_node.appendChild( parent_element  )

        # desactivate all dependencies
        dependencies_root = ( xmldoc.getElementsByTagName("dependencies") or [] )
        for node in dependencies_root:
            copylist_child_Nodes = list(node.childNodes)
            for child_node in copylist_child_Nodes:
                node.removeChild(child_node)
                child_node.unlink()

        newline = xmldoc.createTextNode('\n')
        # add our classpath using system scope
        if self.cli_options.classpath:
            i=0
            dependencies_root = ( xmldoc.getElementsByTagName("dependencies") or [] )
            if dependencies_root:
                for node in dependencies_root:
                    for classpath_element in self.cli_options.classpath[0].split(':'):
                        if classpath_element:
                            dependency_elem = xmldoc.createElement("dependency")
                            dependency_elem.appendChild( self.create_element(xmldoc, "groupId", "gentoo.group.id.tmp"))
                            dependency_elem.appendChild( self.create_element(xmldoc, "artifactId", "gentoo%d" % (i)))
                            dependency_elem.appendChild( self.create_element(xmldoc, "version", "666"))
                            dependency_elem.appendChild( self.create_element(xmldoc, "scope", "system") )
                            dependency_elem.appendChild( self.create_element(xmldoc, "systemPath", classpath_element))
                            node.appendChild(dependency_elem)
                            node.appendChild(newline.cloneNode(deep=True))
                            i += 1

        # overwrite source/target options if any
        # remove version node for all plugins
        if self.cli_options.p_source or self.cli_options.p_target:
            dependencies_root = ( xmldoc.getElementsByTagName("plugin") or [] )
            # remove part
            if len(dependencies_root) > 0:
                for node in dependencies_root:
                    for child_node in node.childNodes:
                        if child_node.nodeName == "version":
                            node.removeChild(child_node)
                            child_node.unlink()

                        if child_node.nodeName == "artifactId":
                            if "maven-compiler-plugin" ==  child_node.childNodes[0].data:
                                node.parentNode.removeChild(node)
                                node.unlink()
				break

            # creation/overwrite part
            plugin_node = self.create_element(xmldoc,"plugin")
            group_node = self.create_element(xmldoc,"groupId","org.apache.maven.plugins")
            artifact_node = self.create_element(xmldoc,"artifactId","maven-compiler-plugin")
            configuration_node = self.create_element(xmldoc,"configuration")
            plugin_node.appendChild(group_node)
            plugin_node.appendChild(artifact_node)
            plugin_node.appendChild(configuration_node)
            if self.cli_options.p_target:
                target_node = self.create_element(xmldoc,"target",self.cli_options.p_target[0])
                configuration_node.appendChild(target_node)

            if self.cli_options.p_source:
                source_node = self.create_element(xmldoc,"source",self.cli_options.p_source[0])
                configuration_node.appendChild(source_node)

            #add maven-compiler-plugin with source and target versions set to plugins node
            project_node = xmldoc.getElementsByTagName("project")[0]
            build_node = self.element_exists(project_node, "build")
            #no build node
            if not build_node:
                build_node = self.create_element(xmldoc,"build")
                #append plugins node
                build_node.appendChild( self.create_element(xmldoc,"plugins") )
                project_node.appendChild(build_node)

            #no plugins node under build_node
            build_plugin_node = self.element_exists(build_node, "plugins")
            if not build_plugin_node:
                build_node.appendChild( self.create_element(xmldoc,"plugins") )
                project_node.appendChild(build_node)             

            plugins_nodes = ( xmldoc.getElementsByTagName("plugins") or [] )

            # no plugins node - this is redundant?
            if len(plugins_nodes) < 1  :
                plugins_node = self.create_element(xmldoc,"plugins")
                plugins_nodes.append(plugins_node)
                
            for plugins_node in plugins_nodes:
                # add our generated plugin node
                #there'll be several plugins nodes in profiles and one directly under build and
                #another under build#pluginManagement node
                plugins_node.appendChild(plugin_node.cloneNode(deep=True))

        self.__write(xmldoc.toxml("utf-8"))

    def element_exists(self,parent_node,element_name):
        element = None
        if element_name:
            for child_node in parent_node.childNodes:
                if child_node.nodeType == child_node.ELEMENT_NODE:
                    if child_node.nodeName == element_name:
                        return child_node            
        return element

    def create_element(self,xmldoc,element_name,text_value=None):
        element = None
        if element_name:
            element = xmldoc.createElement(element_name)
            if text_value:
                text_node = xmldoc.createTextNode(text_value)
                element.appendChild(text_node)

        return element


    def parse(self,in_stream,callback=None,**kwargs):
        from xml.dom.minidom import parseString
        self.mydoc = parseString(in_stream)

        if callback:
            callback(self.mydoc,**kwargs)

# vim: set expandtab tabstop=4 shiftwidth=4 softtabstop=4 nowrap:
