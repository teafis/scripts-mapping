"""
GSHHG LIB provides a Python implementation for the Global Self-consistent Hierarchical High-resolution Geography data
set provided by NOAA under the LGPLv3 (https://www.ngdc.noaa.gov/mgg/shorelines/)
"""

import array
import enum
import io
import sys
import typing


class GSHHGShape:
    """
    Python implementation of the Global Self-consistent Hierarchical High-resolution Geography, GSHHG, data format to
    provide terrain and coastline database information
    """

    # Defines the parameters in the class
    __slots__ = ('header', 'points_x', 'points_y')

    # Defines the number of integers present in the header
    HEADER_LEN = 11

    class LevelType(enum.Enum):
        """
        Enumeration to provide the type of a given shape
        """
        INVALID = -1
        LAND = 1
        LAKE = 2
        ISLAND_IN_LAKE = 3
        POND_IN_ISLAND_IN_LAKE = 4

    def __init__(self, header: bytes):
        """
        Initializes the shape with the provided GSHHG header file for version 2.3.7
        :param header: the bytes provided by the header values
        """
        # Check input values
        if len(header) != self.HEADER_LEN * 4:
            raise ValueError('Header must have 11 4-byte big-endian integers provided')

        # Initialize Parameters
        header_array = array.array('i')
        header_array.frombytes(header)

        if sys.byteorder == 'little':
            header_array.byteswap()

        self.header = header_array
        self.points_x = None
        self.points_y = None

    def header_int(self, i: int) -> int:
        """
        Provides the integer of the header at index i
        :param i: the index to obtain the integer at
        :return: the integer corresponding with the provided index
        """
        return self.header[i]

    @property
    def id(self) -> int:
        """
        Provides the shape unique ID
        :return: the shape id
        """
        return self.header_int(0)

    @property
    def num_points(self) -> int:
        """
        The number of points in the shape
        :return: the number of points in the shape
        """
        return self.header_int(1)

    @property
    def flag(self) -> int:
        """
        Provides the shape flag
        :return: the shape flag
        """
        return self.header_int(2)

    @property
    def west(self) -> float:
        """
        Provides the west-most longitude of the shape
        :return: west-most longitude in degrees
        """
        return self.header_int(3) / 1e6

    @property
    def east(self) -> float:
        """
        Provides the east-most longitude of the shape
        :return: east-most longitude in degrees
        """
        return self.header_int(4) / 1e6

    @property
    def south(self) -> float:
        """
        Provides the south-most latitude of the shape
        :return: south-most latitude in degrees
        """
        return self.header_int(5) / 1e6

    @property
    def north(self) -> float:
        """
        Provides the north-most latitude of the shape
        :return: north-most latitude in degrees
        """
        return self.header_int(6) / 1e6

    @property
    def area(self) -> float:
        """
        Provides the contained polygon area
        :return: the contained area in the polygon in km^2
        """
        return self.header_int(7) / 10

    @property
    def area_full(self) -> float:
        """
        Provides the full contained area area
        :return: the full area of the original polygon in km^2
        """
        return self.header_int(8) / 10

    @property
    def container(self) -> int:
        """
        Provides the container polygon id that contains the current polygon
        :return: the id if it exists, otherwise None
        """
        i = self.header_int(9)
        return i if i != -1 else None

    @property
    def ancestor(self) -> int:
        """
        Provides the ancestor of the polygon in the full-resolution set
        :return: the id of the ancestor if it exists, otherwise None
        """
        i = self.header_int(10)
        return i if i != -1 else None

    @property
    def level(self) -> 'GSHHGShape.LevelType':
        """
        Provides the level portion of the flag to indicate the shape type
        :return: an instance of the shape type enumeration corresponding to the current shape type
        """
        v = self.flag & 0xFF
        try:
            return self.LevelType(v)
        except ValueError as e:
            print('Invalid level type {:d}'.format(v))
            return self.LevelType.INVALID

    def set_points(self, points: bytes) -> None:
        """
        Sets the points instance to the bytes provided
        :param points: the bytes of the data points to add to the class
        """
        if self.points_x is not None or self.points_y is not None:
            raise ValueError('cannot re-set the points objects')
        elif len(points) != self.num_points * 4 * 2:
            raise ValueError('the number of bytes provided ({:d}) does not match the expected ({:d})'.format(
                len(points),
                self.num_points * 4))
        else:
            # Extract the associated byte values to integer arrays
            all_points = array.array('i')
            all_points.frombytes(points)

            # Swap byte order if necessary
            if sys.byteorder == 'little':
                all_points.byteswap()

            # Slice the array into parameters
            points_x = all_points[0::2]
            points_y = all_points[1::2]

            # Check resulting lengths
            if len(points_x) != len(points_y):
                raise ValueError('expected x and y points to have the same length')

            # Assign results
            self.points_x = points_x
            self.points_y = points_y

    def get_lon(self) -> typing.List[float]:
        """
        Returns the longitude values and attempts to compensate for wraparound to close the shape
        :return: a list of floats for the longitude of the shape in degrees
        """
        # Convert the integer values to floats
        lon_vals = [p / 1e6 for p in self.points_x]

        # Determine if an adjustment is needed to close the shape
        adjust_needed = False
        for i in range(1, len(lon_vals)):
            # Determine the difference between two points, and if greater than 170 deg, needs adjustment
            if abs(lon_vals[i] - lon_vals[i-1]) > 170:
                adjust_needed = True
                break

        # Adjust values if needed to try to close the shape
        if adjust_needed:
            for i in range(len(lon_vals)):
                if lon_vals[i] > 180:
                    lon_vals[i] -= 360

        # Return the adjusted longitude values
        return lon_vals

    def get_lat(self) -> typing.List[float]:
        """
        Returns the latitude values
        :return: a list of floats for the latitude of the shape in degrees
        """
        return [p / 1e6 for p in self.points_y]

    @classmethod
    def read_from_stream(cls, data: io.BufferedReader) -> 'GSHHGShape':
        """
        Creates an instance of the GSHHG shape class from raw bytes
        :param data: the input bytes to read in and process
        :return: the shape file associated with the input bytes
        """
        # Define the initial shape definition files based on the header
        shape = GSHHGShape(header=data.read(cls.HEADER_LEN * 4))

        # Read the points into the bytes and set the resulting value
        points = data.read(8 * shape.num_points)
        shape.set_points(points)

        # Return the shape value
        return shape
