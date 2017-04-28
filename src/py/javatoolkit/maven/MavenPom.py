# Copyright 2004-2007 Gentoo Foundation
# Distrubuted under the terms of the GNU General Public Licence v2

# Authors:
# koirky <kiorky@cryptelium.net> The code:
# ali_bush <ali_bush@gentoo.org> Refactored into module.
# Python based POM navigator

# Changelog
# ali_bush <ali_bush@gentoo.org>
# 31/12/07 Refacted by separating MavenPom into namespace
#
# kiorky <kiorky@cryptelium.net>
# 31/05/2007 Add rewrite feature
#
# kiorky <kiorky@cryptelium.net>
# 08/05/2007 initial version

import sys
import io

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
        self.buffer = io.StringIO()
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


    def rewrite(self,xmldoc,**kwargs):
        # desactivate all dependencies
        dependencies_root = ( xmldoc.getElementsByTagName("dependencies") or [] )
        for node in dependencies_root:
            copylist_child_Nodes =list(node.childNodes)
            for child_node in copylist_child_Nodes:
                node.removeChild(child_node)
                child_node.unlink()

        # add our classpath using system scope
        if self.cli_options.classpath:
            i=0
            dependencies_root = ( xmldoc.getElementsByTagName("dependencies") or [] )
            if dependencies_root:
                for node in dependencies_root:
                    for classpath_element in self.cli_options.classpath[0].split(':'):
                        if classpath_element:
                            dependency_elem = xmldoc.createElement("dependency")
                            dependency_elem.appendChild( self.create_element(xmldoc, "groupId", "sexy"))
                            dependency_elem.appendChild( self.create_element(xmldoc, "artifactId", "gentoo%d" % (i)))
                            dependency_elem.appendChild( self.create_element(xmldoc, "version", "666"))
                            dependency_elem.appendChild( self.create_element(xmldoc, "scope", "system"))
                            dependency_elem.appendChild( self.create_element(xmldoc, "systemPath", classpath_element))
                            node.appendChild(dependency_elem)
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

            plugins_nodes = ( xmldoc.getElementsByTagName("plugins") or [] )
            # no plugins node
            if len(plugins_nodes) < 1  :
                plugins_node = self.create_element(xmldoc,"plugins")
                plugins_nodes.append(plugins_node)
                for plugins_node in plugins_nodes:
                    # add our generated plugin node
                    plugins_node.appendChild(plugin_node)

                    # no build node
                    build_nodes = ( xmldoc.getElementsByTagName("build") or [] )
                    if len(build_nodes) < 1 :
                        build_node = self.create_element(xmldoc,"build")
                        build_nodes.append(build_node)
                        # add build node to project_node
                        project_nodes = ( xmldoc.getElementsByTagName("project") or [] )
                        for project_node in project_nodes:
                            project_node.appendChild(build_node)

                    # add plugins structure to the build node
                    for build_node in build_nodes:
                        build_node.appendChild(plugins_node.cloneNode(deep=True))

        self.__write(xmldoc.toxml("utf-8"))


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
