from PtpUploaderException import PtpUploaderException
from Settings import Settings
from TagList import TagList

import re

class ReleaseNameParser:
	def __init__(self, name):
		originalName = name

		# Simply popping the last tag as a group name wouldn't work because of P2P release with multiple dashes in it:
		# Let Me In 2010 DVDRIP READNFO XViD-T0XiC-iNK

		self.Group = ""
		
		name = name.lower()
		name = name.replace( ".", " " )
		name = name.strip()

		# Check if there is a group name in the release name.
		if name.rfind( '-' ) == -1 or name.endswith( "-" ):
			self.Tags = TagList( name.split( " " ) )
		else:
			name = name.replace( "-", " " )
			name = name.strip()
			self.Tags = TagList( name.split( " " ) )
			if self.__HandleSpecialGroupName( [ "d", "z0n3" ] ):
				pass
			elif self.__HandleSpecialGroupName( [ "t0xic", "ink" ] ):
				pass
			elif self.__HandleSpecialGroupName( [ "vh", "prod" ] ):
				pass
			elif name.endswith( " h 264" ): # For release names without group names. E.g.: Critters.1986.720p.WEB-DL.AAC2.0.H.264
				pass
			else:
				self.Group = self.Tags.List.pop()

		if len( self.Tags.List ) <= 0:
			raise PtpUploaderException( "Release name '%s' doesn't contain any tags." % originalName )

		# This is not perfect (eg.: The Legend of 1900), but it doesn't matter if the real year will be included in the tags.
		self.TagsAfterYear = TagList( [] )
		for i in range( len( self.Tags.List ) ):
			if re.match( r"\d\d\d\d", self.Tags.List[ i ] ):
				self.TagsAfterYear.List = self.Tags.List[ i + 1: ]
				break

		self.Scene = self.Group in Settings.SceneReleaserGroup
		
	def __HandleSpecialGroupName(self, groupNameAsTagList):
		if self.Tags.RemoveTagsFromEndIfPossible( groupNameAsTagList ):
			self.Group = "-".join( groupNameAsTagList )
			return True
		
		return False

	def GetSourceAndFormat(self, releaseInfo):
		if releaseInfo.IsCodecSet():
			releaseInfo.Logger.info( "Codec '%s' is already set, not getting from release name." % releaseInfo.Codec )
		elif self.Tags.IsContainsTag( "xvid" ):
			releaseInfo.Codec = "XviD"
		elif self.Tags.IsContainsTag( "divx" ):
			releaseInfo.Codec = "DivX"
		elif self.Tags.IsContainsTag( "x264" ):
			releaseInfo.Codec = "x264"
		elif self.Tags.IsContainsTag( "avc" ) or self.Tags.IsContainsTag( "h264" ) or self.Tags.IsContainsTags( [ "h", "264" ] ):
			releaseInfo.Codec = "H.264"
		elif self.Tags.IsContainsTag( "mpeg2" ) or self.Tags.IsContainsTags( [ "mpeg", "2" ] ):
			releaseInfo.Codec = "MPEG-2"
		elif self.Tags.IsContainsTag( "vc1" ) or self.Tags.IsContainsTags( [ "vc", "1" ] ):
			releaseInfo.Codec = "VC-1"
		else:
			raise PtpUploaderException( "Can't figure out codec from release name '%s'." % releaseInfo.ReleaseName )

		if releaseInfo.IsSourceSet():
			releaseInfo.Logger.info( "Source '%s' is already set, not getting from release name." % releaseInfo.Source )
		elif self.Tags.IsContainsTag( "dvdrip" ):
			releaseInfo.Source = "DVD"
		elif self.Tags.IsContainsTag( "bdrip" ) or self.Tags.IsContainsTag( "bluray" ) or self.Tags.IsContainsTags( [ "blu", "ray" ] ):
			releaseInfo.Source = "Blu-ray"
		elif self.Tags.IsContainsTag( "hddvd" ):
			releaseInfo.Source = "HD-DVD"
		elif self.Tags.IsContainsTag( "hdtv" ):
			releaseInfo.Source = "HDTV"
		elif self.Tags.IsContainsTag( "dvdscr" ):
			releaseInfo.Source = "DVD-Screener"
		elif self.Tags.IsContainsTag( "webdl" ) or self.Tags.IsContainsTags( [ "web", "dl" ] ):
			releaseInfo.Source = "WEB"
		elif self.Tags.IsContainsTag( "brrip" ):
			raise PtpUploaderException( "BRRips are not allowed." )
		else:
			raise PtpUploaderException( "Can't figure out source from release name '%s'." % releaseInfo.ReleaseName )

		if releaseInfo.IsResolutionTypeSet():
			releaseInfo.Logger.info( "Resolution type '%s' is already set, not getting from release name." % releaseInfo.ResolutionType )
		elif self.Tags.IsContainsTag( "720p" ):
			releaseInfo.ResolutionType = "720p"
		elif self.Tags.IsContainsTag( "1080p" ):
			releaseInfo.ResolutionType = "1080p"
		elif self.Tags.IsContainsTag( "1080i" ):
			releaseInfo.ResolutionType = "1080i"
		else:
			releaseInfo.ResolutionType = "Other"

		if len( releaseInfo.RemasterTitle ) <= 0 and self.Tags.IsContainsTag( "remux" ):
			releaseInfo.RemasterTitle = "Remux"

	@staticmethod
	def __IsTagListContainAnythingFromListOfTagList(tagList, listOfTagList):
		for listOfTagListElement in listOfTagList:
			if tagList.IsContainsTags( listOfTagListElement.List ):
				return str( listOfTagListElement )

		return None

	def IsAllowed(self):
		if self.Group in Settings.IgnoreReleaserGroup:
			return "Group '%s' is in your ignore list." % self.Group
		
		if len( Settings.AllowReleaseTag ) > 0:
			match = ReleaseNameParser.__IsTagListContainAnythingFromListOfTagList( self.Tags, Settings.AllowReleaseTag )
			if match is None:
				return "Ignored because didn't match your allowed tags setting."

		match = ReleaseNameParser.__IsTagListContainAnythingFromListOfTagList( self.Tags, Settings.IgnoreReleaseTag )
		if match is not None:
			return "'%s' is on your ignore list." % match

		if len( self.TagsAfterYear.List ) > 0:
			match = ReleaseNameParser.__IsTagListContainAnythingFromListOfTagList( self.TagsAfterYear, Settings.IgnoreReleaseTagAfterYear )
			if match is not None:
				return "'%s' is on your ignore list." % match
		else:
			match = ReleaseNameParser.__IsTagListContainAnythingFromListOfTagList( self.Tags, Settings.IgnoreReleaseTagAfterYear )
			if match is not None:
				return "'%s' is on your ignore list." % match

		return None
